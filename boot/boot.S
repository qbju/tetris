.section .multiboot,"a"
.align 8
header_start:
  .long 0xe85250d6
  .long 0
  .long header_end - header_start
  .long -(0xe85250d6 + (header_end - header_start))
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
