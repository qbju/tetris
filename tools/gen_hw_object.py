"""CPython+llvmlite emits freestanding i386 hardware primitives."""
from __future__ import annotations

import sys
from llvmlite import binding, ir


def build() -> bytes:
    binding.initialize_all_targets()
    binding.initialize_all_asmprinters()
    binding.initialize_native_asmparser()
    module = ir.Module(name="tetris_ui")
    module.triple = "i386-unknown-elf"
    i16, i32, void = ir.IntType(16), ir.IntType(32), ir.VoidType()

    board_type = ir.ArrayType(i32, 240)
    board = ir.GlobalVariable(module, board_type, name="tetris_board")
    board.linkage = "internal"
    board.initializer = ir.Constant(board_type, None)

    get_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name="board_get")
    get_index = get_fn.args[0]
    get_builder = ir.IRBuilder(get_fn.append_basic_block("entry"))
    get_pointer = get_builder.gep(board, [ir.Constant(i32, 0), get_index], inbounds=True)
    get_builder.ret(get_builder.load(get_pointer))

    set_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="board_set")
    set_index, set_value = set_fn.args
    set_builder = ir.IRBuilder(set_fn.append_basic_block("entry"))
    set_pointer = set_builder.gep(board, [ir.Constant(i32, 0), set_index], inbounds=True)
    set_builder.store(set_value, set_pointer)
    set_builder.ret_void()
    # Shared 512-byte sector buffer. LPython owns all filesystem policy.
    buffer_type = ir.ArrayType(i32, 512)
    sector_buffer = ir.GlobalVariable(module, buffer_type, name="fs_sector_buffer")
    sector_buffer.linkage = "internal"
    sector_buffer.initializer = ir.Constant(buffer_type, None)

    buffer_get = ir.Function(module, ir.FunctionType(i32, [i32]), name="fs_buffer_get")
    buffer_get_index = buffer_get.args[0]
    buffer_get_builder = ir.IRBuilder(buffer_get.append_basic_block("entry"))
    buffer_get_pointer = buffer_get_builder.gep(
        sector_buffer, [ir.Constant(i32, 0), buffer_get_index], inbounds=True
    )
    buffer_get_builder.ret(buffer_get_builder.load(buffer_get_pointer))

    buffer_set = ir.Function(module, ir.FunctionType(void, [i32, i32]), name="fs_buffer_set")
    buffer_set_index, buffer_set_value = buffer_set.args
    buffer_set_builder = ir.IRBuilder(buffer_set.append_basic_block("entry"))
    buffer_set_pointer = buffer_set_builder.gep(
        sector_buffer, [ir.Constant(i32, 0), buffer_set_index], inbounds=True
    )
    buffer_set_builder.store(buffer_set_value, buffer_set_pointer)
    buffer_set_builder.ret_void()

    asm_clobbers = ",~{dirflag},~{fpsr},~{flags}"

    def build_port_in(name: str, value_type: ir.IntType, opcode: str) -> None:
        port_fn = ir.Function(module, ir.FunctionType(i32, [i32]), name=name)
        port_builder = ir.IRBuilder(port_fn.append_basic_block("entry"))
        port = port_builder.trunc(port_fn.args[0], i16)
        value = port_builder.asm(
            ir.FunctionType(value_type, [i16]),
            f"{opcode} $1, $0",
            "={ax},{dx}" + asm_clobbers,
            [port],
            side_effect=True,
        )
        port_builder.ret(port_builder.zext(value, i32))

    def build_port_out(name: str, value_type: ir.IntType, opcode: str) -> None:
        port_fn = ir.Function(module, ir.FunctionType(void, [i32, i32]), name=name)
        port_builder = ir.IRBuilder(port_fn.append_basic_block("entry"))
        port = port_builder.trunc(port_fn.args[0], i16)
        value = port_builder.trunc(port_fn.args[1], value_type)
        port_builder.asm(
            ir.FunctionType(void, [value_type, i16]),
            f"{opcode} $0, $1",
            "{ax},{dx}" + asm_clobbers,
            [value, port],
            side_effect=True,
        )
        port_builder.ret_void()

    build_port_in("io_in8", ir.IntType(8), "inb")
    build_port_out("io_out8", ir.IntType(8), "outb")
    build_port_in("io_in16", i16, "inw")
    build_port_out("io_out16", i16, "outw")

    argv_fn = ir.Function(
        module,
        ir.FunctionType(void, [i32, ir.IntType(8).as_pointer().as_pointer()]),
        name="_lpython_set_argv",
    )
    argv_builder = ir.IRBuilder(argv_fn.append_basic_block("entry"))
    argv_builder.ret_void()
    fn = ir.Function(module, ir.FunctionType(void, [i32, i32, i32, i32]), name="ui_put_cell")
    x, y, glyph, colour = fn.args
    block = fn.append_basic_block("entry")
    builder = ir.IRBuilder(block)
    cell = builder.add(builder.mul(y, ir.Constant(i32, 80)), x)
    address = builder.add(ir.Constant(i32, 0xB8000), builder.mul(cell, ir.Constant(i32, 2)))
    pointer = builder.inttoptr(address, i16.as_pointer())
    attribute = builder.shl(colour, ir.Constant(i32, 8))
    value = builder.trunc(builder.or_(glyph, attribute), i16)
    builder.store(value, pointer)
    builder.ret_void()

    target = binding.Target.from_triple(module.triple)
    machine = target.create_target_machine(reloc="static")
    return machine.emit_object(binding.parse_assembly(str(module)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_hw_object.py OUTPUT.o")
    with open(sys.argv[1], "wb") as output:
        output.write(build())
