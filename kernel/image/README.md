# kernel/image

Pure-LPython indexed-color raster API for extensions.

- `image.process` grants access to a shared 65,536-pixel, 8-bit buffer. It provides pixel access, clear/fill, horizontal/vertical flip, and nearest-neighbour scaling to the native framebuffer.
- GIF input has a separate 1MiB stream buffer. `extension_gif_decode(length)` decodes GIF87a/GIF89a global/local palettes, transparency, and LZW into the image buffer, then programs the VGA palette.
- Initial GIF scope: first image frame only, up to 256×256, non-interlaced. Animated playback and interlacing are intentionally deferred.
- Native presentation and GIF palette changes additionally require `framebuffer.native`.

PNG is next; JPEG is intentionally not planned for the kernel decoder.