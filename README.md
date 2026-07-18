# PythonOS Tetris

Bootable, freestanding Tetris experiment.  Handwritten assembly is limited to
the Multiboot2 header, stack setup, and the call to LPython's `kernel_main`.

- LPython: board state, movement and game loop (`kernel/main.py`)
- CPython + llvmlite: builds `ui_put_cell`, an i386 VGA-text renderer
- C: the unavoidable x86 port-I/O boundary for PS/2 keyboard polling

Use the Docker environment after completing its LPython installation:

```sh
docker compose build
docker compose run --rm osdev make run
```

Arrow-left/right move a falling block. This is the playable vertical slice;
add tetromino masks, rotation, line removal and score in LPython next.
