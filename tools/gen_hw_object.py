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

    elf_bytes = Path("build/hello.elf").read_bytes()
    elf_type = ir.ArrayType(i8, len(elf_bytes))
    elf_image = ir.GlobalVariable(module, elf_type, name="embedded_hello_elf")
    elf_image.linkage = "internal"
    elf_image.global_constant = True
    elf_image.initializer = ir.Constant(elf_type, bytearray(elf_bytes))
    elf_size_fn = ir.Function(module, ir.FunctionType(i32, []), name="elf_image_size")
    ir.IRBuilder(elf_size_fn.append_basic_block("entry")).ret(ir.Constant(i32, len(elf_bytes)))
    elf_get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="elf_image_get")
    b = ir.IRBuilder(elf_get_fn.append_basic_block("entry"))
    elf_byte = b.load(b.gep(elf_image, [c0, elf_get_fn.args[0]], inbounds=True))
    b.ret(b.zext(elf_byte, i32))
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

    def out(builder: ir.IRBuilder, port: int, value: int) -> None:
        builder.call(io_out8, [ir.Constant(i32, port), ir.Constant(i32, value)])

    normal_palette = ((0,0,0),(0,0,42),(0,42,0),(0,42,42),(42,0,0),(42,0,42),(42,21,0),(42,42,42),(21,21,21),(21,21,63),(21,63,21),(21,63,63),(63,21,21),(63,21,63),(63,63,21),(63,63,63))
    gray_palette = tuple(((red * 3 + green * 6 + blue) // 10,) * 3 for red, green, blue in normal_palette)
    inverted_palette = tuple((63 - red, 63 - green, 63 - blue) for red, green, blue in normal_palette)
    konami_palette = tuple((min(63, red + blue // 3), green // 4, 0 if colour < 8 else min(63, red + green)) for colour, (red, green, blue) in enumerate(normal_palette))
    # Keep UI foreground entries white and UI background entries black in 01 mode.
    binary_palette = tuple(((0, 0, 0) if colour < 7 else (63, 63, 63)) for colour in range(16))
    golden_palette = tuple((min(63, 12 + red), min(63, 6 + (red + green) // 2), blue // 6) for red, green, blue in normal_palette)
    palette_fn = ir.Function(module, ir.FunctionType(void, [i32]), name="vga_set_palette")
    pb = ir.IRBuilder(palette_fn.append_basic_block("entry"))
    out(pb, 0x3C8, 0)
    is_gray = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 1))
    is_inverted = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 2))
    is_konami = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 3))
    is_binary = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 4))
    is_golden = pb.icmp_signed("==", palette_fn.args[0], ir.Constant(i32, 5))
    for colour_index in range(16):
        for component in range(3):
            normal_value = ir.Constant(i32, normal_palette[colour_index][component])
            gray_value = ir.Constant(i32, gray_palette[colour_index][component])
            inverted_value = ir.Constant(i32, inverted_palette[colour_index][component])
            konami_value = ir.Constant(i32, konami_palette[colour_index][component])
            binary_value = ir.Constant(i32, binary_palette[colour_index][component])
            golden_value = ir.Constant(i32, golden_palette[colour_index][component])
            selected = pb.select(is_gray, gray_value, pb.select(is_inverted, inverted_value, pb.select(is_konami, konami_value, pb.select(is_binary, binary_value, pb.select(is_golden, golden_value, normal_value)))))
            pb.call(io_out8, [ir.Constant(i32, 0x3C9), selected])
    pb.ret_void()

    mode_fn = ir.Function(module, ir.FunctionType(void, []), name="vga_set_mode13")
    b = ir.IRBuilder(mode_fn.append_basic_block("entry"))
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
    b.ret_void()

    ui_buffer_type = ir.ArrayType(i8, 64000)
    ui_backbuffer = ir.GlobalVariable(module, ui_buffer_type, name="ui_backbuffer")
    ui_backbuffer.linkage = "internal"
    ui_backbuffer.initializer = ir.Constant(ui_buffer_type, None)
    ui_target = ir.GlobalVariable(module, i32, name="ui_render_target")
    ui_target.linkage = "internal"
    ui_target.initializer = c0

    target_fn = ir.Function(module, ir.FunctionType(void, [i32]), name="ui_set_render_target")
    target_builder = ir.IRBuilder(target_fn.append_basic_block("entry"))
    target_builder.store(target_fn.args[0], ui_target)
    target_builder.ret_void()
    font_type = ir.ArrayType(i8, 2048)
    font = ir.GlobalVariable(module, font_type, name="tetris_font")
    font.linkage = "internal"
    font.global_constant = True
    font.initializer = ir.Constant(font_type, bytearray(font_bytes()))

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
    screen_pointer = b.inttoptr(b.add(ir.Constant(i32, 0xA0000), pixel_index), i8.as_pointer())
    buffer_pointer = b.gep(ui_backbuffer, [c0, pixel_index], inbounds=True)
    destination = b.select(b.icmp_signed("!=", b.load(ui_target), c0), buffer_pointer, screen_pointer)
    b.store(b.trunc(pixel_colour, i8), destination)
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
    rect_screen_pointer = b.inttoptr(b.add(ir.Constant(i32, 0xA0000), rect_pixel_index), i8.as_pointer())
    rect_buffer_pointer = b.gep(ui_backbuffer, [c0, rect_pixel_index], inbounds=True)
    rect_destination = b.select(b.icmp_signed("!=", b.load(ui_target), c0), rect_buffer_pointer, rect_screen_pointer)
    b.store(b.trunc(rect_colour, i8), rect_destination)
    rect_next = b.add(rect_index, c1)
    b.branch(rect_cond)
    rect_index.add_incoming(rect_next, rect_body)
    b.position_at_end(rect_done)
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
    present_screen_pointer = b.inttoptr(b.add(ir.Constant(i32, 0xA0000), present_index), i8.as_pointer())
    present_target_pixel = b.load(present_buffer_pointer)
    present_screen_pixel = b.load(present_screen_pointer)
    within_reveal = b.icmp_signed("<", present_x, reveal_x)
    pixel_changed = b.icmp_unsigned("!=", present_target_pixel, present_screen_pixel)
    b.cbranch(b.and_(within_reveal, pixel_changed), present_copy, present_next)
    b.position_at_end(present_copy)
    b.store(present_target_pixel, present_screen_pointer)
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