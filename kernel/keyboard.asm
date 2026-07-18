; Generic i386 port-I/O boundary. All device policy lives in LPython.
BITS 32
GLOBAL io_in8
GLOBAL io_out8
GLOBAL io_in16
GLOBAL io_out16
GLOBAL _lpython_set_argv

SECTION .text
io_in8:
    mov edx, [esp + 4]
    xor eax, eax
    in al, dx
    ret

io_out8:
    mov edx, [esp + 4]
    mov eax, [esp + 8]
    out dx, al
    ret

io_in16:
    mov edx, [esp + 4]
    xor eax, eax
    in ax, dx
    ret

io_out16:
    mov edx, [esp + 4]
    mov eax, [esp + 8]
    out dx, ax
    ret

_lpython_set_argv:
    ret
