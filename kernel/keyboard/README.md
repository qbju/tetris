# Build-time keyboard layouts

Every `*.keyboard` file in this directory is parsed by `tools/gen_kernel_source.py` and compiled into the LPython kernel. The files are not needed at runtime.

```ini
name=JIS
27=59,43
```

Each mapping is:

```text
PS/2 set-1 scancode in hexadecimal = normal ASCII, shifted ASCII
```

For example, `27=59,43` maps scancode `0x27` to `;` normally and `+` while Shift is held.

Rules:

- `name` must contain 1 to 12 ASCII characters.
- Scancodes and character values must fit in one byte.
- Unlisted scancodes produce no character, except alphabet keys handled by the common kernel mapping.
- File names determine the stable build order. Reordering or renaming files can change saved layout indices.
- Rebuild the ISO after adding or changing a layout.