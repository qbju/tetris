BUILD := build
KERNEL := $(BUILD)/kernel.elf
ISO := $(BUILD)/pythonos.iso
DATA := storage/pythonos-data.img
LPYTHON_INC := /opt/conda/share/lpython/lib/impure

.PHONY: all run clean
all: $(ISO) $(DATA)

$(BUILD):
	mkdir -p $(BUILD)

# CPython + llvmlite produces an ELF object containing the hot framebuffer
# primitive. This is deliberately a build-time tool, never part of the OS.
$(DATA):
	mkdir -p storage
	truncate -s 4M $@
$(BUILD)/hw.o: tools/gen_hw_object.py | $(BUILD)
	python3 tools/gen_hw_object.py $@

# LPython emits C; final image is a freestanding i386 Multiboot kernel.
$(BUILD)/kernel.c: kernel/main.py | $(BUILD)
	lpython --show-c kernel/main.py > $@

$(BUILD)/kernel.o: $(BUILD)/kernel.c
	clang -target i386-elf -ffreestanding -fno-stack-protector -fno-pic -I$(LPYTHON_INC) -c $< -o $@

$(BUILD)/boot.o: boot/boot.S | $(BUILD)
	clang -target i386-elf -ffreestanding -fno-stack-protector -fno-pic -c $< -o $@

$(KERNEL): $(BUILD)/boot.o $(BUILD)/kernel.o $(BUILD)/hw.o linker.ld
	ld.lld -m elf_i386 -T linker.ld -o $@ $(BUILD)/boot.o $(BUILD)/kernel.o $(BUILD)/hw.o

$(ISO): $(KERNEL) grub/grub.cfg
	mkdir -p $(BUILD)/iso/boot/grub
	cp $(KERNEL) $(BUILD)/iso/boot/kernel.elf
	cp grub/grub.cfg $(BUILD)/iso/boot/grub/grub.cfg
	grub-mkrescue -o $@ $(BUILD)/iso

run: $(ISO) $(DATA)
	qemu-system-x86_64 -cdrom $(ISO) -drive file=$(DATA),format=raw,if=ide,index=0 -serial stdio

clean:
	rm -rf $(BUILD)
