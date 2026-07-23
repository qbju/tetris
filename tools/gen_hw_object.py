"""CPython+llvmlite emits freestanding i386 graphics and hardware primitives."""
from __future__ import annotations

import sys
from pathlib import Path
from llvmlite import binding, ir


# Four-pixel-wide glyphs preserve the existing 80x25 LPython UI layout while
# rendering it into Mode 13h's 320x200 pixel framebuffer.
FONT_4X8 = {
    "0": ("0110", "1001", "1001", "1001", "1001", "1001", "0110", "0000"),
    "1": ("0010", "0110", "0010", "0010", "0010", "0010", "0111", "0000"),
    "2": ("0110", "1001", "0001", "0010", "0100", "1000", "1111", "0000"),
    "3": ("1110", "0001", "0010", "0001", "0001", "1001", "0110", "0000"),
    "4": ("0011", "0101", "1001", "1111", "0001", "0001", "0001", "0000"),
    "5": ("1111", "1000", "1110", "0001", "0001", "1001", "0110", "0000"),
    "6": ("0111", "1000", "1110", "1001", "1001", "1001", "0110", "0000"),
    "7": ("1111", "0001", "0010", "0010", "0100", "0100", "0100", "0000"),
    "8": ("0110", "1001", "1001", "0110", "1001", "1001", "0110", "0000"),
    "9": ("0110", "1001", "1001", "0111", "0001", "0001", "1110", "0000"),
    "A": ("0110", "1001", "1001", "1111", "1001", "1001", "1001", "0000"),
    "B": ("1110", "1001", "1001", "1110", "1001", "1001", "1110", "0000"),
    "C": ("0111", "1000", "1000", "1000", "1000", "1000", "0111", "0000"),
    "D": ("1110", "1001", "1001", "1001", "1001", "1001", "1110", "0000"),
    "E": ("1111", "1000", "1000", "1110", "1000", "1000", "1111", "0000"),
    "F": ("1111", "1000", "1000", "1110", "1000", "1000", "1000", "0000"),
    "G": ("0111", "1000", "1000", "1011", "1001", "1001", "0111", "0000"),
    "H": ("1001", "1001", "1001", "1111", "1001", "1001", "1001", "0000"),
    "I": ("1111", "0010", "0010", "0010", "0010", "0010", "1111", "0000"),
    "J": ("0011", "0001", "0001", "0001", "0001", "1001", "0110", "0000"),
    "K": ("1001", "1010", "1100", "1000", "1100", "1010", "1001", "0000"),
    "L": ("1000", "1000", "1000", "1000", "1000", "1000", "1111", "0000"),
    "M": ("1001", "1111", "1111", "1001", "1001", "1001", "1001", "0000"),
    "N": ("1001", "1101", "1101", "1011", "1011", "1001", "1001", "0000"),
    "O": ("0110", "1001", "1001", "1001", "1001", "1001", "0110", "0000"),
    "P": ("1110", "1001", "1001", "1110", "1000", "1000", "1000", "0000"),
    "Q": ("0110", "1001", "1001", "1001", "1011", "1010", "0101", "0000"),
    "R": ("1110", "1001", "1001", "1110", "1100", "1010", "1001", "0000"),
    "S": ("0111", "1000", "1000", "0110", "0001", "0001", "1110", "0000"),
    "T": ("1111", "0010", "0010", "0010", "0010", "0010", "0010", "0000"),
    "U": ("1001", "1001", "1001", "1001", "1001", "1001", "0110", "0000"),
    "V": ("1001", "1001", "1001", "1001", "1001", "0110", "0110", "0000"),
    "W": ("1001", "1001", "1001", "1001", "1111", "1111", "1001", "0000"),
    "X": ("1001", "1001", "0110", "0010", "0110", "1001", "1001", "0000"),
    "Y": ("1001", "1001", "0110", "0010", "0010", "0010", "0010", "0000"),
    "Z": ("1111", "0001", "0010", "0110", "0100", "1000", "1111", "0000"),
    "!": ("0010", "0010", "0010", "0010", "0010", "0000", "0010", "0000"),
    "\"": ("0101", "0101", "0101", "0000", "0000", "0000", "0000", "0000"),
    "#": ("0101", "1111", "0101", "0101", "1111", "0101", "0000", "0000"),
    "$": ("0010", "0111", "1010", "0110", "0011", "1110", "0010", "0000"),
    "%": ("1001", "0001", "0010", "0010", "0100", "1000", "1001", "0000"),
    "&": ("0110", "1000", "1000", "0110", "1010", "1001", "0111", "0000"),
    "'": ("0010", "0010", "0100", "0000", "0000", "0000", "0000", "0000"),
    "(": ("0001", "0010", "0100", "0100", "0100", "0010", "0001", "0000"),
    ")": ("1000", "0100", "0010", "0010", "0010", "0100", "1000", "0000"),
    "=": ("0000", "1111", "0000", "1111", "0000", "0000", "0000", "0000"),
    "~": ("0000", "0101", "1010", "0000", "0000", "0000", "0000", "0000"),
    "|": ("0010", "0010", "0010", "0010", "0010", "0010", "0010", "0000"),
    "`": ("0100", "0010", "0000", "0000", "0000", "0000", "0000", "0000"),
    "{": ("0011", "0010", "0010", "1100", "0010", "0010", "0011", "0000"),
    "+": ("0000", "0010", "0010", "1111", "0010", "0010", "0000", "0000"),
    "*": ("0000", "1010", "0110", "1111", "0110", "1010", "0000", "0000"),
    "}": ("1100", "0100", "0100", "0011", "0100", "0100", "1100", "0000"),
    "<": ("0001", "0010", "0100", "1000", "0100", "0010", "0001", "0000"),
    "?": ("0110", "1001", "0001", "0010", "0010", "0000", "0010", "0000"),
    "^": ("0010", "0101", "1000", "0000", "0000", "0000", "0000", "0000"),
    "@": ("0110", "1001", "1011", "1011", "1010", "1000", "0111", "0000"),
    "[": ("0111", "0100", "0100", "0100", "0100", "0100", "0111", "0000"),
    ";": ("0000", "0110", "0110", "0000", "0110", "0010", "0100", "0000"),
    "]": ("1110", "0010", "0010", "0010", "0010", "0010", "1110", "0000"),
    ",": ("0000", "0000", "0000", "0000", "0000", "0010", "0010", "0100"),    ":": ("0000", "0110", "0110", "0000", "0110", "0110", "0000", "0000"),
    "-": ("0000", "0000", "0000", "1111", "0000", "0000", "0000", "0000"),
    ".": ("0000", "0000", "0000", "0000", "0000", "0110", "0110", "0000"),
    "/": ("0001", "0001", "0010", "0010", "0100", "0100", "1000", "1000"),
    ">": ("1000", "0100", "0010", "0001", "0010", "0100", "1000", "0000"),
    "_": ("0000", "0000", "0000", "0000", "0000", "0000", "1111", "0000"),
    "\\": ("1000", "1000", "0100", "0100", "0010", "0010", "0001", "0001"),
}


def font_bytes() -> list[int]:
    data = [0] * (256 * 8)
    for char, rows in FONT_4X8.items():
        for row, bits in enumerate(rows):
            # Compress four source columns into three visible columns and keep
            # bit 0 clear as inter-character spacing.
            source = int(bits, 2)
            left = (source >> 3) & 1
            middle = ((source >> 2) | (source >> 1)) & 1
            right = source & 1
            data[ord(char) * 8 + row] = (left << 3) | (middle << 2) | (right << 1)
            if char >= "A" and char <= "Z":
                data[(ord(char) + 32) * 8 + row] = (left << 3) | (middle << 2) | (right << 1)
    # CP437 forms used by the existing UI. Lines use the full cell width and
    # share the same two centre columns vertically, so every corner joins.
    for row in range(8):
        data[219 * 8 + row] = 0xF
        data[186 * 8 + row] = 0x6
    for row in (3, 4):
        data[205 * 8 + row] = 0xF
    for glyph in (201, 187):
        for row in (3, 4):
            data[glyph * 8 + row] = 0xF
        for row in (5, 6, 7):
            data[glyph * 8 + row] = 0x6
    for glyph in (200, 188):
        for row in (0, 1, 2):
            data[glyph * 8 + row] = 0x6
        for row in (3, 4):
            data[glyph * 8 + row] = 0xF
    data[16 * 8 + 3] = 0x2
    data[16 * 8 + 4] = 0x6
    data[16 * 8 + 5] = 0x2
    return data


def build() -> bytes:
    binding.initialize_all_targets()
    binding.initialize_all_asmprinters()
    binding.initialize_native_asmparser()
    module = ir.Module(name="tetris_hw")
    module.triple = "i386-unknown-elf"
    i8, i16, i32, void = ir.IntType(8), ir.IntType(16), ir.IntType(32), ir.VoidType()
    c0, c1, c2, c3, c4, c7, c8 = [ir.Constant(i32, value) for value in (0, 1, 2, 3, 4, 7, 8)]

    # Minimal freestanding string runtime required by LPython's str indexing.
    strlen_fn = ir.Function(module, ir.FunctionType(i32, [i8.as_pointer()]), name="strlen")
    sl_entry = strlen_fn.append_basic_block("entry")
    sl_cond = strlen_fn.append_basic_block("cond")
    sl_body = strlen_fn.append_basic_block("body")
    sl_done = strlen_fn.append_basic_block("done")
    b = ir.IRBuilder(sl_entry)
    b.branch(sl_cond)
    b.position_at_end(sl_cond)
    sl_index = b.phi(i32, name="index")
    sl_index.add_incoming(c0, sl_entry)
    sl_byte = b.load(b.gep(strlen_fn.args[0], [sl_index], inbounds=True))
    b.cbranch(b.icmp_unsigned("!=", sl_byte, ir.Constant(i8, 0)), sl_body, sl_done)
    b.position_at_end(sl_body)
    sl_next = b.add(sl_index, c1)
    b.branch(sl_cond)
    sl_index.add_incoming(sl_next, sl_body)
    b.position_at_end(sl_done)
    b.ret(sl_index)

    str_item_fn = ir.Function(module, ir.FunctionType(i8.as_pointer(), [i8.as_pointer(), i32]), name="_lfortran_str_item")
    b = ir.IRBuilder(str_item_fn.append_basic_block("entry"))
    b.ret(b.gep(str_item_fn.args[0], [b.sub(str_item_fn.args[1], c1)], inbounds=True))

    str_ord_fn = ir.Function(module, ir.FunctionType(i32, [i8.as_pointer()]), name="_lfortran_str_ord_c")
    b = ir.IRBuilder(str_ord_fn.append_basic_block("entry"))
    b.ret(b.zext(b.load(str_ord_fn.args[0]), i32))

    # ELF programs live in TinyFS and are built separately under extension/.
    # Keep this compatibility ABI for the LPython loader without embedding one.
    elf_size_fn = ir.Function(module, ir.FunctionType(i32, []), name="elf_image_size")
    ir.IRBuilder(elf_size_fn.append_basic_block("entry")).ret(ir.Constant(i32, 0))
    elf_get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="elf_image_get")
    ir.IRBuilder(elf_get_fn.append_basic_block("entry")).ret(ir.Constant(i32, 0))
    memory_write_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="physical_write8")
    b = ir.IRBuilder(memory_write_fn.append_basic_block("entry"))
    b.store(b.trunc(memory_write_fn.args[1], i8), b.inttoptr(memory_write_fn.args[0], i8.as_pointer()))
    b.ret_void()
    memory_read_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="physical_read8")
    b = ir.IRBuilder(memory_read_fn.append_basic_block("entry"))
    b.ret(b.zext(b.load(b.inttoptr(memory_read_fn.args[0], i8.as_pointer())), i32))
    call_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="elf_call_entry")
    b = ir.IRBuilder(call_fn.append_basic_block("entry"))
    entry_type = ir.FunctionType(i32, [])
    result = b.call(b.inttoptr(call_fn.args[0], entry_type.as_pointer()), [])
    b.ret(result)
    board_type = ir.ArrayType(i32, 240)
    board = ir.GlobalVariable(module, board_type, name="tetris_board")
    board.linkage = "internal"
    board.initializer = ir.Constant(board_type, None)
    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="board_get")
    b = ir.IRBuilder(get_fn.append_basic_block("entry"))
    b.ret(b.load(b.gep(board, [c0, get_fn.args[0]], inbounds=True)))
    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="board_set")
    b = ir.IRBuilder(set_fn.append_basic_block("entry"))
    b.store(set_fn.args[1], b.gep(board, [c0, set_fn.args[0]], inbounds=True))
    b.ret_void()

    # Keep the shuffled bag in an LLVM-owned global. This avoids relying on
    # freestanding LPython global-array initialization.
    bag_type = ir.ArrayType(i32, 7)
    bag = ir.GlobalVariable(module, bag_type, name="tetris_bag")
    bag.linkage = "internal"
    bag.initializer = ir.Constant(bag_type, None)
    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="bag_get")
    b = ir.IRBuilder(get_fn.append_basic_block("entry"))
    b.ret(b.load(b.gep(bag, [c0, get_fn.args[0]], inbounds=True)))
    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="bag_set")
    b = ir.IRBuilder(set_fn.append_basic_block("entry"))
    b.store(set_fn.args[1], b.gep(bag, [c0, set_fn.args[0]], inbounds=True))
    b.ret_void()

    music_type = ir.ArrayType(i32, 32)
    any_music = ir.GlobalVariable(module, music_type, name="any_music_data")
    any_music.linkage = "internal"
    any_music.initializer = ir.Constant(music_type, None)
    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="any_note_get")
    b = ir.IRBuilder(get_fn.append_basic_block("entry"))
    b.ret(b.load(b.gep(any_music, [c0, get_fn.args[0]], inbounds=True)))
    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="any_note_set")
    b = ir.IRBuilder(set_fn.append_basic_block("entry"))
    b.store(set_fn.args[1], b.gep(any_music, [c0, set_fn.args[0]], inbounds=True))
    b.ret_void()
    name_type = ir.ArrayType(i32, 8)
    any_name = ir.GlobalVariable(module, name_type, name="any_music_name")
    any_name.linkage = "internal"
    any_name.initializer = ir.Constant(name_type, None)
    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="any_name_get")
    b = ir.IRBuilder(get_fn.append_basic_block("entry"))
    b.ret(b.load(b.gep(any_name, [c0, get_fn.args[0]], inbounds=True)))
    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="any_name_set")
    b = ir.IRBuilder(set_fn.append_basic_block("entry"))
    b.store(set_fn.args[1], b.gep(any_name, [c0, set_fn.args[0]], inbounds=True))
    b.ret_void()
    extension_memory_type = ir.ArrayType(i32, 1024)
    extension_memory = ir.GlobalVariable(module, extension_memory_type, name="extension_memory")
    extension_memory.linkage = "internal"
    extension_memory.initializer = ir.Constant(extension_memory_type, None)
    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="extension_memory_get")
    b = ir.IRBuilder(get_fn.append_basic_block("entry"))
    b.ret(b.load(b.gep(extension_memory, [c0, get_fn.args[0]], inbounds=True)))
    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="extension_memory_set")
    b = ir.IRBuilder(set_fn.append_basic_block("entry"))
    b.store(set_fn.args[1], b.gep(extension_memory, [c0, set_fn.args[0]], inbounds=True))
    b.ret_void()
    buffer_type = ir.ArrayType(i32, 512)
    sector_buffer = ir.GlobalVariable(module, buffer_type, name="fs_sector_buffer")
    sector_buffer.linkage = "internal"
    sector_buffer.initializer = ir.Constant(buffer_type, None)
    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="fs_buffer_get")
    b = ir.IRBuilder(get_fn.append_basic_block("entry"))
    b.ret(b.load(b.gep(sector_buffer, [c0, get_fn.args[0]], inbounds=True)))
    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="fs_buffer_set")
    b = ir.IRBuilder(set_fn.append_basic_block("entry"))
    b.store(set_fn.args[1], b.gep(sector_buffer, [c0, set_fn.args[0]], inbounds=True))
    b.ret_void()

    clobbers = ",~{dirflag},~{fpsr},~{flags}"

    def port_in(name: str, typ: ir.IntType, opcode: str) -> ir.Function:
        fn = ir.Function(module, ir.FunctionType(i32, [i32]), name=name)
        b = ir.IRBuilder(fn.append_basic_block("entry"))
        port = b.trunc(fn.args[0], i16)
        value = b.asm(ir.FunctionType(typ, [i16]), f"{opcode} $1, $0", "={ax},{dx}" + clobbers, [port], side_effect=True)
        b.ret(b.zext(value, i32))
        return fn

    def port_out(name: str, typ: ir.IntType, opcode: str) -> ir.Function:
        fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name=name)
        b = ir.IRBuilder(fn.append_basic_block("entry"))
        b.asm(ir.FunctionType(void, [typ, i16]), f"{opcode} $0, $1", "{ax},{dx}" + clobbers, [b.trunc(fn.args[1], typ), b.trunc(fn.args[0], i16)], side_effect=True)
        b.ret_void()
        return fn

    io_in8 = port_in("io_in8", i8, "inb")
    io_out8 = port_out("io_out8", i8, "outb")
    port_in("io_in16", i16, "inw")
    port_out("io_out16", i16, "outw")

    argv_fn = ir.Function(module, ir.FunctionType(void, [i32, i8.as_pointer().as_pointer()]), name="_lpython_set_argv")
    ir.IRBuilder(argv_fn.append_basic_block("entry")).ret_void()

    framebuffer_active = ir.GlobalVariable(module, i32, name="framebuffer_active")
    framebuffer_active.linkage = "internal"
    framebuffer_active.initializer = c0
    framebuffer_address = ir.GlobalVariable(module, i32, name="framebuffer_address")
    framebuffer_address.linkage = "internal"
    framebuffer_address.initializer = c0
    framebuffer_pitch = ir.GlobalVariable(module, i32, name="framebuffer_pitch")
    framebuffer_pitch.linkage = "internal"
    framebuffer_pitch.initializer = c0
    framebuffer_width = ir.GlobalVariable(module, i32, name="framebuffer_width")
    framebuffer_width.linkage = "internal"
    framebuffer_width.initializer = c0
    framebuffer_height = ir.GlobalVariable(module, i32, name="framebuffer_height")
    framebuffer_height.linkage = "internal"
    framebuffer_height.initializer = c0

    fb_init = ir.Function(module, ir.FunctionType(void, [i32]), name="framebuffer_init")
    fb_entry = fb_init.append_basic_block("entry")
    fb_loop = fb_init.append_basic_block("loop")
    fb_check = fb_init.append_basic_block("check")
    fb_setup = fb_init.append_basic_block("setup")
    fb_next = fb_init.append_basic_block("next")
    fb_done = fb_init.append_basic_block("done")
    b = ir.IRBuilder(fb_entry)
    mbi = fb_init.args[0]
    total_size = b.load(b.inttoptr(mbi, i32.as_pointer()))
    first_tag = b.add(mbi, ir.Constant(i32, 8))
    end_address = b.add(mbi, total_size)
    b.branch(fb_loop)
    b.position_at_end(fb_loop)
    tag_address = b.phi(i32, name="tag")
    tag_address.add_incoming(first_tag, fb_entry)
    before_end = b.icmp_unsigned("<", tag_address, end_address)
    b.cbranch(before_end, fb_check, fb_done)
    b.position_at_end(fb_check)
    tag_type = b.load(b.inttoptr(tag_address, i32.as_pointer()))
    is_end = b.icmp_signed("==", tag_type, c0)
    is_framebuffer = b.icmp_signed("==", tag_type, ir.Constant(i32, 8))
    b.cbranch(is_end, fb_done, fb_setup)
    b.position_at_end(fb_setup)
    tag_bpp = b.zext(b.load(b.inttoptr(b.add(tag_address, ir.Constant(i32, 28)), i8.as_pointer())), i32)
    tag_width = b.load(b.inttoptr(b.add(tag_address, ir.Constant(i32, 20)), i32.as_pointer()))
    tag_height = b.load(b.inttoptr(b.add(tag_address, ir.Constant(i32, 24)), i32.as_pointer()))
    valid_bpp = b.icmp_signed("==", tag_bpp, ir.Constant(i32, 32))
    valid_width = b.icmp_unsigned(">=", tag_width, ir.Constant(i32, 640))
    valid_height = b.icmp_unsigned(">=", tag_height, ir.Constant(i32, 480))
    valid_tag = b.and_(is_framebuffer, b.and_(valid_bpp, b.and_(valid_width, valid_height)))
    setup_store = fb_init.append_basic_block("setup.store")
    b.cbranch(valid_tag, setup_store, fb_next)
    b.position_at_end(setup_store)
    fb_addr_low = b.load(b.inttoptr(b.add(tag_address, ir.Constant(i32, 8)), i32.as_pointer()))
    fb_pitch_value = b.load(b.inttoptr(b.add(tag_address, ir.Constant(i32, 16)), i32.as_pointer()))
    b.store(fb_addr_low, framebuffer_address)
    b.store(fb_pitch_value, framebuffer_pitch)
    b.store(tag_width, framebuffer_width)
    b.store(tag_height, framebuffer_height)
    b.store(c1, framebuffer_active)
    b.branch(fb_done)
    b.position_at_end(fb_next)
    tag_size = b.load(b.inttoptr(b.add(tag_address, c4), i32.as_pointer()))
    aligned_size = b.and_(b.add(tag_size, c7), ir.Constant(i32, -8))
    next_tag = b.add(tag_address, aligned_size)
    b.branch(fb_loop)
    tag_address.add_incoming(next_tag, fb_next)
    b.position_at_end(fb_done)
    b.ret_void()
    def out(builder: ir.IRBuilder, port: int, value: int) -> None:
        builder.call(io_out8, [ir.Constant(i32, port), ir.Constant(i32, value)])

    normal_palette = ((0,0,0),(0,0,42),(0,42,0),(0,42,42),(42,0,0),(42,0,42),(42,21,0),(42,42,42),(21,21,21),(21,21,63),(21,63,21),(21,63,63),(63,21,21),(63,21,63),(63,63,21),(63,63,63))
    gray_palette = tuple(((red * 3 + green * 6 + blue) // 10,) * 3 for red, green, blue in normal_palette)
    inverted_palette = tuple((63 - red, 63 - green, 63 - blue) for red, green, blue in normal_palette)
    konami_palette = tuple((min(63, red + blue // 3), green // 4, 0 if colour < 8 else min(63, red + green)) for colour, (red, green, blue) in enumerate(normal_palette))
    # Keep UI foreground entries white and UI background entries black in 01 mode.
    binary_palette = tuple(((0, 0, 0) if colour < 7 else (63, 63, 63)) for colour in range(16))
    golden_palette = tuple((min(63, 12 + red), min(63, 6 + (red + green) // 2), blue // 6) for red, green, blue in normal_palette)
    fb_palette_type = ir.ArrayType(i32, 256)
    fb_palette = ir.GlobalVariable(module, fb_palette_type, name="framebuffer_palette")
    fb_palette.linkage = "internal"
    fb_palette.initializer = ir.Constant(fb_palette_type, None)
    recolour_fn = ir.Function(module, ir.FunctionType(void, []), name="ui_recolour_frontbuffer")
    palette_fn = ir.Function(module, ir.FunctionType(void, [i32]), name="vga_set_palette")
    pb = ir.IRBuilder(palette_fn.append_basic_block("entry"))
    out(pb, 0x3C8, 0)
    is_gray = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 1))
    is_inverted = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 2))
    is_konami = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 3))
    is_binary = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 4))
    is_golden = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 5))
    for colour_index in range(16):
        selected_components = []
        for component in range(3):
            normal_value = ir.Constant(i32, normal_palette[colour_index][component])
            gray_value = ir.Constant(i32, gray_palette[colour_index][component])
            inverted_value = ir.Constant(i32, inverted_palette[colour_index][component])
            konami_value = ir.Constant(i32, konami_palette[colour_index][component])
            binary_value = ir.Constant(i32, binary_palette[colour_index][component])
            golden_value = ir.Constant(i32, golden_palette[colour_index][component])
            selected = pb.select(is_gray, gray_value, pb.select(is_inverted, inverted_value, pb.select(is_konami, konami_value, pb.select(is_binary, binary_value, pb.select(is_golden, golden_value, normal_value)))))
            pb.call(io_out8, [ir.Constant(i32, 0x3C9), selected])
            selected_components.append(selected)
        red8 = pb.sdiv(pb.mul(selected_components[0], ir.Constant(i32, 255)), ir.Constant(i32, 63))
        green8 = pb.sdiv(pb.mul(selected_components[1], ir.Constant(i32, 255)), ir.Constant(i32, 63))
        blue8 = pb.sdiv(pb.mul(selected_components[2], ir.Constant(i32, 255)), ir.Constant(i32, 63))
        packed_rgb = pb.or_(pb.shl(red8, ir.Constant(i32, 16)), pb.or_(pb.shl(green8, ir.Constant(i32, 8)), blue8))
        pb.store(packed_rgb, pb.gep(fb_palette, [c0, ir.Constant(i32, colour_index)], inbounds=True))
    pb.call(recolour_fn, [])
    pb.ret_void()

    palette_entry_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32]), name="ui_set_palette_entry")
    palette_index, palette_red, palette_green, palette_blue = palette_entry_fn.args
    eb = ir.IRBuilder(palette_entry_fn.append_basic_block("entry"))
    eb.call(io_out8, [ir.Constant(i32, 0x3C8), palette_index])
    eb.call(io_out8, [ir.Constant(i32, 0x3C9), palette_red])
    eb.call(io_out8, [ir.Constant(i32, 0x3C9), palette_green])
    eb.call(io_out8, [ir.Constant(i32, 0x3C9), palette_blue])
    red8 = eb.sdiv(eb.mul(palette_red, ir.Constant(i32, 255)), ir.Constant(i32, 63))
    green8 = eb.sdiv(eb.mul(palette_green, ir.Constant(i32, 255)), ir.Constant(i32, 63))
    blue8 = eb.sdiv(eb.mul(palette_blue, ir.Constant(i32, 255)), ir.Constant(i32, 63))
    entry_rgb = eb.or_(eb.shl(red8, ir.Constant(i32, 16)), eb.or_(eb.shl(green8, ir.Constant(i32, 8)), blue8))
    valid_entry = eb.and_(eb.icmp_signed(">=", palette_index, c0), eb.icmp_signed("<", palette_index, ir.Constant(i32, 256)))
    entry_store = palette_entry_fn.append_basic_block("store")
    entry_done = palette_entry_fn.append_basic_block("done")
    eb.cbranch(valid_entry, entry_store, entry_done)
    eb.position_at_end(entry_store)
    eb.store(entry_rgb, eb.gep(fb_palette, [c0, palette_index], inbounds=True))
    eb.call(recolour_fn, [])
    eb.branch(entry_done)
    eb.position_at_end(entry_done)
    eb.ret_void()
    mode_fn = ir.Function(module, ir.FunctionType(void, []), name="vga_set_mode13")
    mode_entry = mode_fn.append_basic_block("entry")
    mode_program = mode_fn.append_basic_block("program")
    mode_done = mode_fn.append_basic_block("done")
    b = ir.IRBuilder(mode_entry)
    b.cbranch(b.icmp_signed("==", b.load(framebuffer_active), c0), mode_program, mode_done)
    b.position_at_end(mode_program)
    out(b, 0x3C2, 0x63)
    for index, value in enumerate((0x03, 0x01, 0x0F, 0x00, 0x0E)):
        out(b, 0x3C4, index); out(b, 0x3C5, value)
    # Unlock CRTC registers 0-7 and 0x11 before programming timing values.
    out(b, 0x3D4, 0x03)
    crtc_03 = b.call(io_in8, [ir.Constant(i32, 0x3D5)])
    b.call(io_out8, [ir.Constant(i32, 0x3D5), b.or_(crtc_03, ir.Constant(i32, 0x80))])
    out(b, 0x3D4, 0x11)
    crtc_11 = b.call(io_in8, [ir.Constant(i32, 0x3D5)])
    b.call(io_out8, [ir.Constant(i32, 0x3D5), b.and_(crtc_11, ir.Constant(i32, 0x7F))])
    for index, value in enumerate((0x5F,0x4F,0x50,0x82,0x54,0x80,0xBF,0x1F,0x00,0x41,0x00,0x00,0x00,0x00,0x00,0x00,0x9C,0x8E,0x8F,0x28,0x40,0x96,0xB9,0xA3,0xFF)):
        out(b, 0x3D4, index); out(b, 0x3D5, value)
    for index, value in enumerate((0x00,0x00,0x00,0x00,0x00,0x40,0x05,0x0F,0xFF)):
        out(b, 0x3CE, index); out(b, 0x3CF, value)
    # Attribute Controller writes require an index/value pair after resetting
    # its flip-flop through input-status register 0x3DA.
    for index, value in enumerate(tuple(range(16)) + (0x41, 0x00, 0x0F, 0x00)):
        b.call(io_in8, [ir.Constant(i32, 0x3DA)])
        out(b, 0x3C0, index)
        out(b, 0x3C0, value)
    b.call(io_in8, [ir.Constant(i32, 0x3DA)])
    out(b, 0x3C0, 0x20)
    b.call(palette_fn, [ir.Constant(i32, 0)])
    b.branch(mode_done)
    b.position_at_end(mode_done)
    b.call(palette_fn, [ir.Constant(i32, 0)])
    b.ret_void()

    ui_buffer_type = ir.ArrayType(i8, 64000)
    ui_backbuffer = ir.GlobalVariable(module, ui_buffer_type, name="ui_backbuffer")
    ui_backbuffer.linkage = "internal"
    ui_backbuffer.initializer = ir.Constant(ui_buffer_type, None)

    ui_childbuffer = ir.GlobalVariable(module, ui_buffer_type, name="ui_childbuffer")
    ui_childbuffer.linkage = "internal"
    ui_childbuffer.initializer = ir.Constant(ui_buffer_type, None)
    ui_target = ir.GlobalVariable(module, i32, name="ui_render_target")
    ui_target.linkage = "internal"
    ui_target.initializer = c0

    ui_frontbuffer = ir.GlobalVariable(module, ui_buffer_type, name="ui_frontbuffer")
    ui_frontbuffer.linkage = "internal"
    ui_frontbuffer.initializer = ir.Constant(ui_buffer_type, None)

    native_surface_type = ir.ArrayType(i8, 640 * 480)
    native_surface = ir.GlobalVariable(module, native_surface_type, name="ui_native_surface")
    native_surface.linkage = "internal"
    native_surface.initializer = ir.Constant(native_surface_type, None)
    native_composing = ir.GlobalVariable(module, i32, name="ui_native_composing")
    native_composing.linkage = "internal"
    native_composing.initializer = c0

    plot_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32]), name="ui_plot_physical")
    plot_x, plot_y, plot_colour = plot_fn.args
    plot_entry = plot_fn.append_basic_block("entry")
    plot_vga = plot_fn.append_basic_block("vga")
    plot_fb = plot_fn.append_basic_block("framebuffer")
    plot_done = plot_fn.append_basic_block("done")
    b = ir.IRBuilder(plot_entry)
    logical_index = b.add(b.mul(plot_y, ir.Constant(i32, 320)), plot_x)
    b.store(b.trunc(plot_colour, i8), b.gep(ui_frontbuffer, [c0, logical_index], inbounds=True))
    b.cbranch(b.icmp_signed("!=", b.load(framebuffer_active), c0), plot_fb, plot_vga)
    b.position_at_end(plot_vga)
    vga_pointer = b.inttoptr(b.add(ir.Constant(i32, 0xA0000), logical_index), i8.as_pointer())
    b.store(b.trunc(plot_colour, i8), vga_pointer)
    b.branch(plot_done)
    b.position_at_end(plot_fb)
    rgb = b.load(b.gep(fb_palette, [c0, b.and_(plot_colour, ir.Constant(i32, 255))], inbounds=True))
    physical_x = b.mul(plot_x, c2)
    physical_y = b.add(b.mul(plot_y, c2), ir.Constant(i32, 40))
    row_address = b.add(b.load(framebuffer_address), b.mul(physical_y, b.load(framebuffer_pitch)))
    pixel_address = b.add(row_address, b.mul(physical_x, c4))
    pitch_value = b.load(framebuffer_pitch)
    for address_offset in (c0, c4):
        b.store(rgb, b.inttoptr(b.add(pixel_address, address_offset), i32.as_pointer()))
        b.store(rgb, b.inttoptr(b.add(b.add(pixel_address, pitch_value), address_offset), i32.as_pointer()))
    b.branch(plot_done)
    b.position_at_end(plot_done)
    b.ret_void()

    recolour_entry = recolour_fn.append_basic_block("entry")
    recolour_cond = recolour_fn.append_basic_block("cond")
    recolour_body = recolour_fn.append_basic_block("body")
    recolour_done = recolour_fn.append_basic_block("done")
    rb = ir.IRBuilder(recolour_entry)
    rb.cbranch(rb.icmp_signed("!=", rb.load(framebuffer_active), c0), recolour_cond, recolour_done)
    rb.position_at_end(recolour_cond)
    recolour_index = rb.phi(i32, name="index")
    recolour_index.add_incoming(c0, recolour_entry)
    rb.cbranch(rb.icmp_signed("<", recolour_index, ir.Constant(i32, 64000)), recolour_body, recolour_done)
    rb.position_at_end(recolour_body)
    recolour_x = rb.srem(recolour_index, ir.Constant(i32, 320))
    recolour_y = rb.sdiv(recolour_index, ir.Constant(i32, 320))
    recolour_colour = rb.zext(rb.load(rb.gep(ui_frontbuffer, [c0, recolour_index], inbounds=True)), i32)
    rb.call(plot_fn, [recolour_x, recolour_y, recolour_colour])
    recolour_next = rb.add(recolour_index, c1)
    rb.branch(recolour_cond)
    recolour_index.add_incoming(recolour_next, recolour_body)
    rb.position_at_end(recolour_done)
    rb.ret_void()
    store_pixel_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32, i32]), name="ui_store_pixel")
    store_x, store_y, store_index, store_colour, store_target = store_pixel_fn.args
    store_entry = store_pixel_fn.append_basic_block("entry")
    store_buffer = store_pixel_fn.append_basic_block("buffer")
    store_screen = store_pixel_fn.append_basic_block("screen")
    store_done = store_pixel_fn.append_basic_block("done")
    b = ir.IRBuilder(store_entry)
    b.cbranch(b.icmp_signed("==", store_target, c0), store_screen, store_buffer)
    b.position_at_end(store_buffer)
    is_child_target = b.icmp_signed("==", store_target, c2)
    buffer_pointer = b.select(is_child_target, b.gep(ui_childbuffer, [c0, store_index], inbounds=True), b.gep(ui_backbuffer, [c0, store_index], inbounds=True))
    b.store(b.trunc(store_colour, i8), buffer_pointer)
    b.branch(store_done)
    b.position_at_end(store_screen)
    b.call(plot_fn, [store_x, store_y, store_colour])
    b.branch(store_done)
    b.position_at_end(store_done)
    b.ret_void()
    target_fn = ir.Function(module, ir.FunctionType(void, [i32]), name="ui_set_render_target")
    target_builder = ir.IRBuilder(target_fn.append_basic_block("entry"))
    target_builder.store(target_fn.args[0], ui_target)
    target_builder.ret_void()
    font_type = ir.ArrayType(i8, 2048)
    font = ir.GlobalVariable(module, font_type, name="tetris_font")
    font.linkage = "internal"
    font.global_constant = True
    font.initializer = ir.Constant(font_type, bytearray(font_bytes()))

    # Direct physical framebuffer access restricted to the two 40px letterbox
    # bars. Extensions cannot overwrite the central 640x400 OS surface here.
    native_plot_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32]), name="ui_native_plot")
    native_x, native_y, native_colour = native_plot_fn.args
    native_entry = native_plot_fn.append_basic_block("entry")
    native_store = native_plot_fn.append_basic_block("store")
    native_buffer = native_plot_fn.append_basic_block("buffer")
    native_screen = native_plot_fn.append_basic_block("screen")
    native_done = native_plot_fn.append_basic_block("done")
    b = ir.IRBuilder(native_entry)
    native_valid_x = b.and_(b.icmp_signed(">=", native_x, c0), b.icmp_signed("<", native_x, ir.Constant(i32, 640)))
    native_valid_y = b.and_(b.icmp_signed(">=", native_y, c0), b.icmp_signed("<", native_y, ir.Constant(i32, 480)))
    native_valid = b.and_(b.icmp_signed("!=", b.load(framebuffer_active), c0), b.and_(native_valid_x, native_valid_y))
    b.cbranch(native_valid, native_store, native_done)
    b.position_at_end(native_store)
    b.cbranch(b.icmp_signed("!=", b.load(native_composing), c0), native_buffer, native_screen)
    b.position_at_end(native_buffer)
    native_index = b.add(b.mul(native_y, ir.Constant(i32, 640)), native_x)
    b.store(b.trunc(native_colour, i8), b.gep(native_surface, [c0, native_index], inbounds=True))
    b.branch(native_done)
    b.position_at_end(native_screen)
    native_rgb = b.load(b.gep(fb_palette, [c0, b.and_(native_colour, ir.Constant(i32, 255))], inbounds=True))
    native_address = b.add(b.load(framebuffer_address), b.add(b.mul(native_y, b.load(framebuffer_pitch)), b.mul(native_x, c4)))
    b.store(native_rgb, b.inttoptr(native_address, i32.as_pointer()))
    b.branch(native_done)
    b.position_at_end(native_done)
    b.ret_void()

    native_begin_fn = ir.Function(module, ir.FunctionType(void, []), name="ui_native_begin")
    b = ir.IRBuilder(native_begin_fn.append_basic_block("entry"))
    b.store(c1, native_composing)
    b.ret_void()

    native_end_fn = ir.Function(module, ir.FunctionType(void, []), name="ui_native_end")
    ne_entry = native_end_fn.append_basic_block("entry")
    ne_cond = native_end_fn.append_basic_block("cond")
    ne_body = native_end_fn.append_basic_block("body")
    ne_done = native_end_fn.append_basic_block("done")
    b = ir.IRBuilder(ne_entry)
    b.store(c0, native_composing)
    b.branch(ne_cond)
    b.position_at_end(ne_cond)
    ne_index = b.phi(i32, name="index")
    ne_index.add_incoming(c0, ne_entry)
    b.cbranch(b.icmp_signed("<", ne_index, ir.Constant(i32, 640 * 480)), ne_body, ne_done)
    b.position_at_end(ne_body)
    ne_x = b.srem(ne_index, ir.Constant(i32, 640))
    ne_y = b.sdiv(ne_index, ir.Constant(i32, 640))
    ne_colour = b.zext(b.load(b.gep(native_surface, [c0, ne_index], inbounds=True)), i32)
    ne_rgb = b.load(b.gep(fb_palette, [c0, ne_colour], inbounds=True))
    ne_address = b.add(b.load(framebuffer_address), b.add(b.mul(ne_y, b.load(framebuffer_pitch)), b.mul(ne_x, c4)))
    b.store(ne_rgb, b.inttoptr(ne_address, i32.as_pointer()))
    ne_next = b.add(ne_index, c1)
    b.branch(ne_cond)
    ne_index.add_incoming(ne_next, ne_body)
    b.position_at_end(ne_done)
    b.ret_void()
    native_rect_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32, i32]), name="ui_native_fill_rect")
    nr_x, nr_y, nr_width, nr_height, nr_colour = native_rect_fn.args
    nr_entry = native_rect_fn.append_basic_block("entry")
    nr_cond = native_rect_fn.append_basic_block("cond")
    nr_body = native_rect_fn.append_basic_block("body")
    nr_done = native_rect_fn.append_basic_block("done")
    b = ir.IRBuilder(nr_entry)
    nr_total = b.mul(nr_width, nr_height)
    b.branch(nr_cond)
    b.position_at_end(nr_cond)
    nr_index = b.phi(i32, name="index")
    nr_index.add_incoming(c0, nr_entry)
    b.cbranch(b.icmp_signed("<", nr_index, nr_total), nr_body, nr_done)
    b.position_at_end(nr_body)
    b.call(native_plot_fn, [b.add(nr_x, b.srem(nr_index, nr_width)), b.add(nr_y, b.sdiv(nr_index, nr_width)), nr_colour])
    nr_next = b.add(nr_index, c1)
    b.branch(nr_cond)
    nr_index.add_incoming(nr_next, nr_body)
    b.position_at_end(nr_done)
    b.ret_void()
    native_restore_fn = ir.Function(module, ir.FunctionType(void, []), name="ui_native_restore_surface")
    ns_entry = native_restore_fn.append_basic_block("entry")
    ns_cond = native_restore_fn.append_basic_block("cond")
    ns_body = native_restore_fn.append_basic_block("body")
    ns_done = native_restore_fn.append_basic_block("done")
    b = ir.IRBuilder(ns_entry)
    b.branch(ns_cond)
    b.position_at_end(ns_cond)
    ns_index = b.phi(i32, name="index")
    ns_index.add_incoming(c0, ns_entry)
    b.cbranch(b.icmp_signed("<", ns_index, ir.Constant(i32, 640 * 480)), ns_body, ns_done)
    b.position_at_end(ns_body)
    ns_x = b.srem(ns_index, ir.Constant(i32, 640))
    ns_y = b.sdiv(ns_index, ir.Constant(i32, 640))
    ns_in_surface = b.and_(b.icmp_signed(">=", ns_y, ir.Constant(i32, 40)), b.icmp_signed("<", ns_y, ir.Constant(i32, 440)))
    ns_source_x = b.sdiv(ns_x, c2)
    ns_source_y = b.sdiv(b.sub(ns_y, ir.Constant(i32, 40)), c2)
    ns_source_index = b.add(b.mul(ns_source_y, ir.Constant(i32, 320)), ns_source_x)
    ns_safe_index = b.select(ns_in_surface, ns_source_index, c0)
    ns_surface_colour = b.zext(b.load(b.gep(ui_frontbuffer, [c0, ns_safe_index], inbounds=True)), i32)
    ns_colour = b.select(ns_in_surface, ns_surface_colour, c0)
    b.call(native_plot_fn, [ns_x, ns_y, ns_colour])
    ns_next = b.add(ns_index, c1)
    b.branch(ns_cond)
    ns_index.add_incoming(ns_next, ns_body)
    b.position_at_end(ns_done)
    b.ret_void()
    native_blit_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="ui_native_blit_child")
    nb_x, nb_y = native_blit_fn.args
    nb_entry = native_blit_fn.append_basic_block("entry")
    nb_cond = native_blit_fn.append_basic_block("cond")
    nb_body = native_blit_fn.append_basic_block("body")
    nb_done = native_blit_fn.append_basic_block("done")
    b = ir.IRBuilder(nb_entry)
    b.branch(nb_cond)
    b.position_at_end(nb_cond)
    nb_index = b.phi(i32, name="index")
    nb_index.add_incoming(c0, nb_entry)
    b.cbranch(b.icmp_signed("<", nb_index, ir.Constant(i32, 64000)), nb_body, nb_done)
    b.position_at_end(nb_body)
    nb_local_x = b.srem(nb_index, ir.Constant(i32, 320))
    nb_local_y = b.sdiv(nb_index, ir.Constant(i32, 320))
    nb_colour = b.zext(b.load(b.gep(ui_childbuffer, [c0, nb_index], inbounds=True)), i32)
    b.call(native_plot_fn, [b.add(nb_x, nb_local_x), b.add(nb_y, nb_local_y), nb_colour])
    nb_next = b.add(nb_index, c1)
    b.branch(nb_cond)
    nb_index.add_incoming(nb_next, nb_body)
    b.position_at_end(nb_done)
    b.ret_void()
    bar_plot_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32]), name="ui_letterbox_plot")
    bar_x, bar_y, bar_colour = bar_plot_fn.args
    bar_entry = bar_plot_fn.append_basic_block("entry")
    bar_store = bar_plot_fn.append_basic_block("store")
    bar_done = bar_plot_fn.append_basic_block("done")
    b = ir.IRBuilder(bar_entry)
    x_valid = b.and_(b.icmp_signed(">=", bar_x, c0), b.icmp_signed("<", bar_x, ir.Constant(i32, 640)))
    y_valid = b.and_(b.icmp_signed(">=", bar_y, c0), b.icmp_signed("<", bar_y, ir.Constant(i32, 480)))
    in_bar = b.or_(b.icmp_signed("<", bar_y, ir.Constant(i32, 40)), b.icmp_signed(">=", bar_y, ir.Constant(i32, 440)))
    can_draw = b.and_(b.icmp_signed("!=", b.load(framebuffer_active), c0), b.and_(x_valid, b.and_(y_valid, in_bar)))
    b.cbranch(can_draw, bar_store, bar_done)
    b.position_at_end(bar_store)
    bar_rgb = b.load(b.gep(fb_palette, [c0, b.and_(bar_colour, ir.Constant(i32, 255))], inbounds=True))
    bar_address = b.add(b.load(framebuffer_address), b.add(b.mul(bar_y, b.load(framebuffer_pitch)), b.mul(bar_x, c4)))
    b.store(bar_rgb, b.inttoptr(bar_address, i32.as_pointer()))
    b.branch(bar_done)
    b.position_at_end(bar_done)
    b.ret_void()

    bar_rect_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32, i32]), name="ui_letterbox_fill_rect")
    bar_rect_x, bar_rect_y, bar_rect_width, bar_rect_height, bar_rect_colour = bar_rect_fn.args
    br_entry = bar_rect_fn.append_basic_block("entry")
    br_cond = bar_rect_fn.append_basic_block("cond")
    br_body = bar_rect_fn.append_basic_block("body")
    br_done = bar_rect_fn.append_basic_block("done")
    b = ir.IRBuilder(br_entry)
    br_total = b.mul(bar_rect_width, bar_rect_height)
    b.branch(br_cond)
    b.position_at_end(br_cond)
    br_index = b.phi(i32, name="index")
    br_index.add_incoming(c0, br_entry)
    b.cbranch(b.icmp_signed("<", br_index, br_total), br_body, br_done)
    b.position_at_end(br_body)
    br_x = b.add(bar_rect_x, b.srem(br_index, bar_rect_width))
    br_y = b.add(bar_rect_y, b.sdiv(br_index, bar_rect_width))
    b.call(bar_plot_fn, [br_x, br_y, bar_rect_colour])
    br_next = b.add(br_index, c1)
    b.branch(br_cond)
    br_index.add_incoming(br_next, br_body)
    b.position_at_end(br_done)
    b.ret_void()

    bar_cell_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32]), name="ui_letterbox_put_cell")
    bar_cell_x, bar_cell_y, bar_glyph, bar_attribute = bar_cell_fn.args
    bc_entry = bar_cell_fn.append_basic_block("entry")
    bc_row_cond = bar_cell_fn.append_basic_block("row.cond")
    bc_row_body = bar_cell_fn.append_basic_block("row.body")
    bc_col_cond = bar_cell_fn.append_basic_block("col.cond")
    bc_col_body = bar_cell_fn.append_basic_block("col.body")
    bc_col_next = bar_cell_fn.append_basic_block("col.next")
    bc_row_next = bar_cell_fn.append_basic_block("row.next")
    bc_done = bar_cell_fn.append_basic_block("done")
    b = ir.IRBuilder(bc_entry)
    b.branch(bc_row_cond)
    b.position_at_end(bc_row_cond)
    bc_row = b.phi(i32, name="row")
    bc_row.add_incoming(c0, bc_entry)
    b.cbranch(b.icmp_signed("<", bc_row, c8), bc_row_body, bc_done)
    b.position_at_end(bc_row_body)
    bc_pattern = b.load(b.gep(font, [c0, b.add(b.mul(bar_glyph, c8), bc_row)], inbounds=True))
    b.branch(bc_col_cond)
    b.position_at_end(bc_col_cond)
    bc_col = b.phi(i32, name="col")
    bc_col.add_incoming(c0, bc_row_body)
    b.cbranch(b.icmp_signed("<", bc_col, c4), bc_col_body, bc_row_next)
    b.position_at_end(bc_col_body)
    bc_shift = b.sub(ir.Constant(i8, 3), b.trunc(bc_col, i8))
    bc_bit = b.and_(bc_pattern, b.shl(ir.Constant(i8, 1), bc_shift))
    bc_fg = b.and_(bar_attribute, ir.Constant(i32, 15))
    bc_bg = b.and_(b.lshr(bar_attribute, c4), ir.Constant(i32, 15))
    bc_colour = b.select(b.icmp_unsigned("!=", bc_bit, ir.Constant(i8, 0)), bc_fg, bc_bg)
    bc_px = b.add(bar_cell_x, b.mul(bc_col, c2))
    bc_py = b.add(bar_cell_y, b.mul(bc_row, c2))
    b.call(bar_plot_fn, [bc_px, bc_py, bc_colour])
    b.call(bar_plot_fn, [b.add(bc_px, c1), bc_py, bc_colour])
    b.call(bar_plot_fn, [bc_px, b.add(bc_py, c1), bc_colour])
    b.call(bar_plot_fn, [b.add(bc_px, c1), b.add(bc_py, c1), bc_colour])
    b.branch(bc_col_next)
    b.position_at_end(bc_col_next)
    bc_next_col = b.add(bc_col, c1)
    b.branch(bc_col_cond)
    bc_col.add_incoming(bc_next_col, bc_col_next)
    b.position_at_end(bc_row_next)
    bc_next_row = b.add(bc_row, c1)
    b.branch(bc_row_cond)
    bc_row.add_incoming(bc_next_row, bc_row_next)
    b.position_at_end(bc_done)
    b.ret_void()
    native_cell_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32]), name="ui_native_put_cell")
    nc_x, nc_y, nc_glyph, nc_attribute = native_cell_fn.args
    nc_entry = native_cell_fn.append_basic_block("entry")
    nc_row_cond = native_cell_fn.append_basic_block("row.cond")
    nc_row_body = native_cell_fn.append_basic_block("row.body")
    nc_col_cond = native_cell_fn.append_basic_block("col.cond")
    nc_col_body = native_cell_fn.append_basic_block("col.body")
    nc_col_next = native_cell_fn.append_basic_block("col.next")
    nc_row_next = native_cell_fn.append_basic_block("row.next")
    nc_done = native_cell_fn.append_basic_block("done")
    b = ir.IRBuilder(nc_entry)
    b.branch(nc_row_cond)
    b.position_at_end(nc_row_cond)
    nc_row = b.phi(i32, name="row")
    nc_row.add_incoming(c0, nc_entry)
    b.cbranch(b.icmp_signed("<", nc_row, c8), nc_row_body, nc_done)
    b.position_at_end(nc_row_body)
    nc_pattern = b.load(b.gep(font, [c0, b.add(b.mul(nc_glyph, c8), nc_row)], inbounds=True))
    b.branch(nc_col_cond)
    b.position_at_end(nc_col_cond)
    nc_col = b.phi(i32, name="col")
    nc_col.add_incoming(c0, nc_row_body)
    b.cbranch(b.icmp_signed("<", nc_col, c4), nc_col_body, nc_row_next)
    b.position_at_end(nc_col_body)
    nc_shift = b.sub(ir.Constant(i8, 3), b.trunc(nc_col, i8))
    nc_bit = b.and_(nc_pattern, b.shl(ir.Constant(i8, 1), nc_shift))
    nc_fg = b.and_(nc_attribute, ir.Constant(i32, 15))
    nc_bg = b.and_(b.lshr(nc_attribute, c4), ir.Constant(i32, 15))
    nc_colour = b.select(b.icmp_unsigned("!=", nc_bit, ir.Constant(i8, 0)), nc_fg, nc_bg)
    nc_px = b.add(nc_x, b.mul(nc_col, c2))
    nc_py = b.add(nc_y, b.mul(nc_row, c2))
    b.call(native_plot_fn, [nc_px, nc_py, nc_colour])
    b.call(native_plot_fn, [b.add(nc_px, c1), nc_py, nc_colour])
    b.call(native_plot_fn, [nc_px, b.add(nc_py, c1), nc_colour])
    b.call(native_plot_fn, [b.add(nc_px, c1), b.add(nc_py, c1), nc_colour])
    b.branch(nc_col_next)
    b.position_at_end(nc_col_next)
    nc_next_col = b.add(nc_col, c1)
    b.branch(nc_col_cond)
    nc_col.add_incoming(nc_next_col, nc_col_next)
    b.position_at_end(nc_row_next)
    nc_next_row = b.add(nc_row, c1)
    b.branch(nc_row_cond)
    nc_row.add_incoming(nc_next_row, nc_row_next)
    b.position_at_end(nc_done)
    b.ret_void()
    fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32]), name="ui_put_cell")
    x, y, glyph, colour = fn.args
    entry = fn.append_basic_block("entry")
    row_cond = fn.append_basic_block("row.cond")
    row_body = fn.append_basic_block("row.body")
    col_cond = fn.append_basic_block("col.cond")
    col_body = fn.append_basic_block("col.body")
    col_next = fn.append_basic_block("col.next")
    row_next = fn.append_basic_block("row.next")
    done = fn.append_basic_block("done")
    b = ir.IRBuilder(entry)
    b.branch(row_cond)
    b.position_at_end(row_cond)
    row = b.phi(i32, name="row")
    row.add_incoming(c0, entry)
    b.cbranch(b.icmp_signed("<", row, c8), row_body, done)
    b.position_at_end(row_body)
    font_index = b.add(b.mul(glyph, c8), row)
    pattern = b.load(b.gep(font, [c0, font_index], inbounds=True))
    b.branch(col_cond)
    b.position_at_end(col_cond)
    col = b.phi(i32, name="col")
    col.add_incoming(c0, row_body)
    b.cbranch(b.icmp_signed("<", col, c4), col_body, row_next)
    b.position_at_end(col_body)
    shift = b.sub(ir.Constant(i8, 3), b.trunc(col, i8))
    bit = b.and_(pattern, b.shl(ir.Constant(i8, 1), shift))
    fg = b.and_(colour, ir.Constant(i32, 15))
    bg = b.and_(b.lshr(colour, ir.Constant(i32, 4)), ir.Constant(i32, 15))
    pixel_colour = b.select(b.icmp_unsigned("!=", bit, ir.Constant(i8, 0)), fg, bg)
    pixel_y = b.add(b.mul(y, c8), row)
    pixel_x = b.add(b.mul(x, c4), col)
    pixel_index = b.add(b.mul(pixel_y, ir.Constant(i32, 320)), pixel_x)
    b.call(store_pixel_fn, [pixel_x, pixel_y, pixel_index, pixel_colour, b.load(ui_target)])

    b.branch(col_next)
    b.position_at_end(col_next)
    next_col = b.add(col, c1)
    b.branch(col_cond)
    col.add_incoming(next_col, col_next)
    b.position_at_end(row_next)
    next_row = b.add(row, c1)
    b.branch(row_cond)
    row.add_incoming(next_row, row_next)
    b.position_at_end(done)
    b.ret_void()

    # Pixel-accurate filled rectangles for extensions and square QR modules.
    rect_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32, i32]), name="ui_fill_rect")
    rect_x, rect_y, rect_width, rect_height, rect_colour = rect_fn.args
    rect_entry = rect_fn.append_basic_block("entry")
    rect_cond = rect_fn.append_basic_block("cond")
    rect_body = rect_fn.append_basic_block("body")
    rect_done = rect_fn.append_basic_block("done")
    b = ir.IRBuilder(rect_entry)
    rect_total = b.mul(rect_width, rect_height)
    b.branch(rect_cond)
    b.position_at_end(rect_cond)
    rect_index = b.phi(i32, name="index")
    rect_index.add_incoming(c0, rect_entry)
    b.cbranch(b.icmp_signed("<", rect_index, rect_total), rect_body, rect_done)
    b.position_at_end(rect_body)
    rect_pixel_x = b.add(rect_x, b.srem(rect_index, rect_width))
    rect_pixel_y = b.add(rect_y, b.sdiv(rect_index, rect_width))
    rect_pixel_index = b.add(b.mul(rect_pixel_y, ir.Constant(i32, 320)), rect_pixel_x)
    b.call(store_pixel_fn, [rect_pixel_x, rect_pixel_y, rect_pixel_index, rect_colour, b.load(ui_target)])

    rect_next = b.add(rect_index, c1)
    b.branch(rect_cond)
    rect_index.add_incoming(rect_next, rect_body)
    b.position_at_end(rect_done)
    b.ret_void()
    # Copy a readable 1:1 viewport from the offscreen child surface.
    blit_fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32]), name="ui_blit_window")
    blit_x, blit_y, blit_width, blit_height = blit_fn.args
    blit_entry = blit_fn.append_basic_block("entry")
    blit_cond = blit_fn.append_basic_block("cond")
    blit_body = blit_fn.append_basic_block("body")
    blit_done = blit_fn.append_basic_block("done")
    b = ir.IRBuilder(blit_entry)
    blit_total = b.mul(blit_width, blit_height)
    b.branch(blit_cond)
    b.position_at_end(blit_cond)
    blit_index = b.phi(i32, name="index")
    blit_index.add_incoming(c0, blit_entry)
    b.cbranch(b.icmp_signed("<", blit_index, blit_total), blit_body, blit_done)
    b.position_at_end(blit_body)
    local_x = b.srem(blit_index, blit_width)
    local_y = b.sdiv(blit_index, blit_width)
    # Preserve the child's native 320x200 logical pixels. Cropping is much
    # more readable than shrinking 4x8 text into a tiny window.
    source_x = local_x
    source_y = local_y
    source_index = b.add(b.mul(source_y, ir.Constant(i32, 320)), source_x)
    target_x = b.add(blit_x, local_x)
    target_y = b.add(blit_y, local_y)
    target_index = b.add(b.mul(target_y, ir.Constant(i32, 320)), target_x)
    source_pointer = b.gep(ui_childbuffer, [c0, source_index], inbounds=True)
    b.call(store_pixel_fn, [target_x, target_y, target_index, b.zext(b.load(source_pointer), i32), b.load(ui_target)])

    blit_next = b.add(blit_index, c1)
    b.branch(blit_cond)
    blit_index.add_incoming(blit_next, blit_body)
    b.position_at_end(blit_done)
    b.ret_void()
    present_fn = ir.Function(module, ir.FunctionType(void, [i32]), name="ui_present_diff")
    reveal_x = present_fn.args[0]
    present_entry = present_fn.append_basic_block("entry")
    present_cond = present_fn.append_basic_block("cond")
    present_body = present_fn.append_basic_block("body")
    present_copy = present_fn.append_basic_block("copy")
    present_next = present_fn.append_basic_block("next")
    present_done = present_fn.append_basic_block("done")
    b = ir.IRBuilder(present_entry)
    b.branch(present_cond)
    b.position_at_end(present_cond)
    present_index = b.phi(i32, name="index")
    present_index.add_incoming(c0, present_entry)
    b.cbranch(b.icmp_signed("<", present_index, ir.Constant(i32, 64000)), present_body, present_done)
    b.position_at_end(present_body)
    present_x = b.srem(present_index, ir.Constant(i32, 320))
    present_buffer_pointer = b.gep(ui_backbuffer, [c0, present_index], inbounds=True)
    present_screen_pointer = b.gep(ui_frontbuffer, [c0, present_index], inbounds=True)
    present_target_pixel = b.load(present_buffer_pointer)
    present_screen_pixel = b.load(present_screen_pointer)
    within_reveal = b.icmp_signed("<", present_x, reveal_x)
    pixel_changed = b.icmp_unsigned("!=", present_target_pixel, present_screen_pixel)
    b.cbranch(b.and_(within_reveal, pixel_changed), present_copy, present_next)
    b.position_at_end(present_copy)
    present_y = b.sdiv(present_index, ir.Constant(i32, 320))
    b.call(plot_fn, [present_x, present_y, b.zext(present_target_pixel, i32)])
    b.branch(present_next)
    b.position_at_end(present_next)
    present_next_index = b.add(present_index, c1)
    b.branch(present_cond)
    present_index.add_incoming(present_next_index, present_next)
    b.position_at_end(present_done)
    b.ret_void()
    target = binding.Target.from_triple(module.triple)
    machine = target.create_target_machine(reloc="static")
    return machine.emit_object(binding.parse_assembly(str(module)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_hw_object.py OUTPUT.o")
    with open(sys.argv[1], "wb") as output:
        output.write(build())