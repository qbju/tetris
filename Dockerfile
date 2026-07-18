# LPython is supplied as the official conda-forge binary: this keeps the image
# build below interactive-agent command limits and avoids compiling LPython.
FROM condaforge/miniforge3:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libc6-dev-i386 clang lld nasm grub-pc-bin xorriso qemu-system-x86 make \
    binutils-dev && \
    rm -rf /var/lib/apt/lists/*

RUN conda install -y -n base -c conda-forge lpython llvmlite && \
    conda clean -afy

WORKDIR /work
