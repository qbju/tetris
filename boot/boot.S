.section .multiboot,"a"
.align 8
header_start:
  .long 0xe85250d6
  .long 0
  .long header_end - header_start
  .long -(0xe85250d6 + (header_end - header_start))
  # Multiboot2 framebuffer request: 640x480x32. GRUB may choose a compatible mode.
  .short 5
  .short 0
  .long 20
  .long 640
  .long 480
  .long 32
  .long 0
  .short 0
  .short 0
  .long 8
header_end:

.section .text
.global _start
_start:
  cli
  mov $stack_top, %esp
  xor %ebp, %ebp
  push %ebx
  call framebuffer_init
  add $4, %esp
  push $0
  push $0
  call main
  add $8, %esp
1: hlt
  jmp 1b

.section .bss
.align 16
stack:
  .skip 16384
stack_top:
