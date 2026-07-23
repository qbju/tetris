# TETRIS OS Extension API

Extensions are LPython source files placed directly in `extension/`. The build generator concatenates them into the kernel and derives the symbol prefix from the filename. For `CLOCK.PY`, the prefix is `ext_clock`.

## Minimal extension

```python
# permissions: settings.read background events notify messages

ext_clock_last: i32 = -1


def ext_clock_enter() -> None:
    global ext_clock_last
    ext_clock_last = -1


def ext_clock_update() -> None:
    pass


def ext_clock_draw() -> None:
    clear_screen(0x10)
    text(2, 2, 67, 0x0F)


def ext_clock_key(key: i32) -> i32:
    if key == 0x01:
        return 1
    return 0


def ext_clock_exit() -> None:
    pass
```

All five lifecycle functions are currently required:

- `*_enter()` initializes the extension whenever it is opened.
- `*_update()` runs on every kernel loop while the extension is active.
- `*_draw()` redraws the extension page when requested.
- `*_key(scancode)` receives PC set-1 make codes.
- `*_exit()` releases extension state.

`key()` return values:

- `0`: remain open.
- `1`: close and return to the extension list.
- `2`: close and return directly to the home menu.
- `3`: remain open and request a redraw.

Escape is also handled by the kernel as close. Extensions that need Escape internally should consume their own state before returning.

## Coordinates and rendering

The logical canvas is 320x200 indexed colour. The framebuffer backend scales it to 640x400 and centres it vertically in the 640x480 framebuffer.

- `ui_put_cell(x, y, glyph, colour)`: draw one 4x8 glyph. Cell coordinates are 80x25.
- `text(x, y, character, colour)`: preferred text helper. A foreground-only colour inherits the normal navy background.
- `ui_fill_rect(x, y, width, height, colour)`: fill logical pixels.
- `clear_screen(colour)`: fill all 80x25 cells.
- `ui_set_palette_entry(index, red, green, blue)`: set one palette entry; RGB components are 0..63.
- `vga_set_palette(mode)`: apply a built-in theme.
- `ui_set_render_target(0|1)`: select physical/front output or the 320x200 offscreen extension surface.
- `ui_blit_window(x, y, width, height)`: copy a 1:1 top-left viewport from the offscreen child surface into a window rectangle.
- `ui_present_diff(reveal_x)`: copy changed pixels from the backbuffer up to logical x coordinate `reveal_x`.

Colour attributes used by `ui_put_cell` follow `0xBGFG`: high nibble background, low nibble foreground. Raw pixel functions use a palette index.

## High-level convenience API

Prefer these helpers over character loops and packed-value decoding:

```python
extension_draw_text(2, 4, "HELLO WORLD", 0x0F)
extension_draw_text_centered(8, "READY", 0x0E)

target: i32 = extension_find("CLOCK.PY")
reply: i32 = extension_send_message_named("CLOCK.PY", 10, 42)

now: i32 = extension_now_ms()
dx: i32 = extension_mouse_dx(mouse_packet)
dy: i32 = extension_mouse_dy(mouse_packet)
buttons: i32 = extension_mouse_buttons(mouse_packet)
extension_play_pitch(8, 10)
```

- String drawing clips safely at the 80-column boundary and returns the number of drawn characters.
- `extension_find()` is ASCII case-insensitive and returns -1 when absent.
- Named messaging uses the same `messages` permission and receiver contract as ID-based messaging.
- `extension_now_ms()` converts the PIT clock to milliseconds.
- Mouse helpers sign-extend PS/2 deltas.
- `extension_play_pitch()` converts the music-editor pitch number to a PC-speaker divisor.
## Native 640x480 framebuffer

Declare `framebuffer.native` to use the checked wrappers:

```python
# permissions: framebuffer.native

extension_native_fill_rect(40, 40, 240, 120, 1)
extension_native_draw_text(56, 56, "NATIVE 640X480", 0x0E)
```

- `extension_native_fill_rect(x, y, width, height, colour)`
- `extension_native_draw_text(x, y, message, colour)`

Unsafe low-level primitives are also available for graphics backends:

- `ui_native_plot(x, y, colour)`
- `ui_native_fill_rect(x, y, width, height, colour)`
- `ui_native_put_cell(x, y, glyph, colour)`

Coordinates are physical framebuffer pixels over the complete 640x480 surface. These writes bypass the 320x200 compositor and may be overwritten by a later normal UI redraw. Persistent native overlays must redraw themselves from a background callback or participate in a custom compositor. Low-level functions intentionally bypass extension permission checks; prefer the checked wrappers for ordinary extensions.

`WINDOWCURSOR.PY` supports a launcher plus up to three simultaneous child windows. Clicking a window focuses it, title bars drag, X closes one child, and Shift+Arrow moves the active window. Plain arrows are delivered to the active child.
## Physical letterbox bars

The 640x480 framebuffer centres the logical 640x400 OS surface between two physical 40px black bars. Extensions can draw only inside these bars through a clipped API:

```python
extension_letterbox_fill(0, 0)  # top, y=0..39
extension_letterbox_fill(1, 0)  # bottom, y=440..479
extension_letterbox_draw_text(0, 0, 2, "TOP STATUS", 0x0E)
extension_letterbox_draw_text(1, 1, 2, "BACKGROUND TASK ACTIVE", 0x0A)
```

- `extension_letterbox_fill(bar, colour)`: fill the top (`0`) or bottom (`1`) bar.
- `extension_letterbox_draw_text(bar, row, x, message, colour)`: draw an 8x16 physical-cell string. There are 80 columns and two rows per bar.
- `extension_letterbox_clear()`: restore both bars to black.
- `ui_letterbox_fill_rect(x, y, width, height, colour)`: low-level physical-pixel rectangle.
- `ui_letterbox_put_cell(x, y, glyph, colour)`: low-level 8x16 glyph at a physical pixel origin.

Low-level writes are clipped to x=0..639 and the two bar ranges, so this API cannot overwrite the central OS surface. It is active only with the 640x480 framebuffer; VGA Mode 13h fallback has no extra bar pixels.

See `extension/LETTERBOXDEMO.PY` for a background status-bar example. It keeps a spinner alive after the foreground extension closes and uses B to toggle the bars.
## Keyboard and mouse

- `scancode_ascii(key)`: convert a set-1 scancode using the current Shift state; returns 0 for non-text keys.
- `keyboard_shifted`: 1 while either Shift key is held.
- `keyboard_control`: 1 while Ctrl is held.
- `ps2_mouse_init()`: enable the PS/2 mouse once before polling.
- `ps2_mouse_poll()`: returns 0 when no complete packet is available. A packet has bit 31 set, buttons in bits 0..2, unsigned X byte in bits 8..15, and unsigned Y byte in bits 16..23. Sign extension is the caller's responsibility.

Common scancodes: Escape `0x01`, Backspace `0x0E`, Enter `0x1C`, Space `0x39`, Up `0x48`, Left `0x4B`, Right `0x4D`, Down `0x50`, Delete `0x53`.

Keyboard repeat is controlled by the kernel: 300ms initial delay and 60ms repeat interval.

## Time and sound

`system_periods` is the monotonic PIT clock in 10ms units. Prefer deadline comparisons against it.

- `rtc_seconds_of_day()`: RTC wall-clock seconds since midnight.
- `sound_tone(divisor, duration)`: enqueue a short PC-speaker effect; duration is in PIT periods.
- `sound_sequence(note0, duration0, note1, duration1, note2, duration2, count)`: enqueue up to three notes.
- `speaker_start(divisor)` / `speaker_stop()`: direct PC-speaker control. Prefer the asynchronous sound helpers.
- `pitch_divisor(pitch)` and `divisor_pitch(divisor)`: conversion helpers used by the music editor.

The kernel calls `sound_update()` itself. An extension should not busy-wait for sound.

## Settings and permissions

Declare capabilities at the top of the source:

```python
# permissions: settings.read background events notify messages settings.write settings.save autostart
```

Capabilities are opt-in and generated at build time:

- `settings.read`: use `extension_setting_get()`.
- `settings.write`: change a setting with `extension_setting_set()`.
- `settings.save`: automatically persist successful changes.
- `autostart`: set or clear the calling extension as the boot extension.
- `background`: enable or disable the calling extension background callback.
- `events`: receive OS event callbacks.
- `notify`: publish an OS notification.
- `messages`: send direct messages to another extension.
- `storage.read`: read the calling extension private persistent sector.
- `storage.write`: create, change, or clear that private persistent sector.
- `framebuffer.native`: use the permission-checked 640x480 physical framebuffer wrappers.

Keys:

| Key | Setting | Range |
|---:|---|---:|
| 0 | Colour mode | 0..5 |
| 1 | Gravity, 10ms periods | 10..100 |
| 2 | Control mode | 0..1 |
| 3 | BGM volume | 0..10 |
| 4 | SE volume | 0..10 |
| 5 | Debug enabled | 0..1 |
| 6 | Clock enabled | 0..1 |
| 7 | Ghost enabled | 0..1 |
| 8 | Music mode | 0..2 |
| 100 | Calling extension autostart | 0..1 |

`extension_setting_get(key)` returns the value or a negative error. `extension_setting_set(key, value)` returns 0 on success and a negative value for missing context, unknown key, denied permission, invalid value, or storage failure. Colour changes apply immediately.

The hidden OS shortcut is Shift+Enter on an extension in the extension list. It toggles the selected extension as the boot extension without exposing an item on the normal Settings pages.

During the boot loading bar, press Tab for a one-time safe boot. The configured autostart entry is preserved but skipped for that boot.

## Background execution

Declare `background`, add the optional callback, then enable it from `enter()` or another callback:

```python
# permissions: background

def ext_example_enter() -> None:
    extension_background_set(1)


def ext_example_background() -> None:
    # Keep this short and non-blocking.
    pass
```

`extension_background_set(1)` enables the calling extension; `extension_background_set(0)` disables it. The function returns 0 on success or a negative permission/context error. Enabled callbacks run once per kernel loop even when another screen or extension is active. State is not persisted across reboot. The scheduler currently uses a 32-bit mask, so background scheduling supports extension IDs 0..31.

Do not draw continuously from `*_background()`. Use it for state, deadlines, messages, and notifications; request visible work through the notification API or the foreground lifecycle.

## OS events

Declare `events` and implement the optional callback:

```python
# permissions: events

def ext_example_event(event: i32, value: i32) -> None:
    if event == 1:
        # value is the number of lines cleared at once.
        pass
```

Events are delivered synchronously in extension registry order, including to extensions that are not open or background-enabled.

| Event | Name | Value |
|---:|---|---|
| 1 | `LINE_CLEAR` | Number of lines cleared simultaneously |
| 2 | `EXTENSION_OPEN` | Opened extension ID |
| 3 | `EXTENSION_CLOSE` | Closed extension ID |
| 4 | `GAME_START` | Game mode: 0 endless, 1 marathon, 2 sprint |
| 5 | `PIECE_LOCK` | Locked tetromino kind |

Event callbacks must remain short. Emitting another open/close action from an event callback can recursively emit events.

## Extension-to-extension messages

Declare `messages` on the sender. Receivers implement an optional message callback:

```python
# Sender
result: i32 = extension_send_message(target_id, 100, 42)

# Receiver
def ext_receiver_message(sender: i32, topic: i32, value: i32) -> i32:
    if topic == 100:
        return value + 1
    return -1
```

`extension_send_message(target, topic, value)` is synchronous and returns the receiver's result. Errors are `-1` for denied/no sender context, `-2` for an invalid target, and `-3` when the target has no message callback. The receiver executes with its own identity and permissions; the sender context is restored afterward.

## Notifications

Declare `notify` and use the string helper. Text is truncated to 16 characters:

```python
# permissions: notify

extension_notification_show_text("HELLO", 0x3F, 300)
```

- `extension_notification_show_text(message, colour, duration)`: preferred string API.
- `extension_notification_char_set(position, character)`: low-level API that stages one character at position 0..15.
- `extension_notification_show(length, colour, duration)`: display text previously staged with the low-level API.

Duration is in 10ms PIT periods; `300` is three seconds. The string API is supported by the current LPython C backend and links without a hosted C runtime.

The popup displays the source extension filename and message. Only one extension notification is active at a time; a newer notification replaces it. Staging uses shared scratch slots 960..975 and the displayed copy uses 976..991, so extensions must reserve those indices.

Notifications coexist with achievement popups in separate vertical regions and trigger a redraw when shown or expired.
## Extension discovery and composition

- `extension_count()`: number of compiled extensions.
- `extension_name_length(id)` / `extension_name_char(id, position)`: inspect filenames.
- `extension_enter(id)`, `extension_update(id)`, `extension_draw(id)`, `extension_key(id, key)`, `extension_exit(id)`: host another extension.
- `extension_window_host_id()`: ID of `WINDOWCURSOR.PY`, or -1.

The dispatcher preserves the caller ID and permission mask across nested extension calls. A host therefore does not inherit a child's permissions, and a child does not inherit its host's permissions.

An extension can optionally provide all three transition hooks:

- `*_transition_enabled() -> i32`
- `*_transition_begin() -> None`
- `*_transition_step() -> i32`

The first matching transition provider becomes the OS transition provider. `step()` returns the horizontal reveal position from 0 through 320.

## Scratch memory and music data

- `extension_memory_get(index)` / `extension_memory_set(index, value)`: shared 1024-element `i32` scratch area.
- `any_note_get(index)` / `any_note_set(index, value)`: access 32 custom music note slots.
- `any_name_get(index)` / `any_name_set(index, value)`: access the eight-character custom music name.

The scratch area is shared by every extension and is not preserved across reboot. Coordinate ranges with a hosting extension before assigning offsets.

## Private persistent extension storage

Declare `storage.read` and/or `storage.write`. Each extension receives 500 bytes selected by a stable hash of its filename:

```python
# permissions: storage.read storage.write

counter: i32 = extension_storage_get_u32(0)
extension_storage_set_u32(0, counter + 1)
extension_storage_set(4, 123)
value: i32 = extension_storage_get(4)
```

- `extension_storage_get(index)` / `extension_storage_set(index, value)`: byte access, index 0..499.
- `extension_storage_get_u32(index)` / `extension_storage_set_u32(index, value)`: little-endian 32-bit access, index 0..496.
- `extension_storage_clear()`: zero all 500 user bytes.

For third-party extensions, prefer the namespaced key/value interface:

```python
# permissions: storage.read storage.write

launches: i32 = extension_storage_kv_get("launches", 0)
extension_storage_kv_set("launches", launches + 1)
exists: i32 = extension_storage_kv_has("launches")
extension_storage_kv_delete("launches")
```

- Keys are printable ASCII, 1..15 characters, and are compared exactly.
- Each extension has up to 25 records containing a signed 32-bit value.
- The filename-derived private namespace is applied automatically; an extension cannot select another extension's namespace through this API.
- `-6` from `extension_storage_kv_set()` means all 25 records are occupied.
- Do not mix the KV API with byte-offset access in the same extension, because both intentionally use the same private 500-byte payload.

Reads from a never-created area return zero. Successful writes return 0; negative values report denied permission, invalid range, disk failure, or a hash-slot collision.

### Multi-sector `.KV` format

For extensions that need more than 25 compact keys, a separate virtual `<EXTENSION>.KV` store is available:

```python
# permissions: storage.read storage.write

score: i32 = extension_kvfile_get("high-score", 0)
extension_kvfile_set("high-score", score + 100)
exists: i32 = extension_kvfile_has("high-score")
extension_kvfile_delete("high-score")
```

- One isolated eight-sector `.KV` area per extension.
- 112 exact-name records per extension.
- Printable ASCII keys of 1..23 characters and signed 32-bit values.
- A full extension fingerprint in the header rejects namespace-slot collisions.
- Each value has a fingerprint-bound integrity word; `-7` reports a damaged record.
- `.KV` uses sectors 16384..32767 and is independent of the compact 500-byte KV store.
- The current format is a kernel-managed virtual file and is not listed in the user-facing TinyFS directory. Filename-derived storage remains stable if registry ordering changes, but renaming an extension intentionally gives it a new storage identity.

The implementation uses sectors 256..8447 of the 16MiB disk. A header stores the full 31-bit filename fingerprint, so a slot collision is rejected instead of exposing another extension's bytes.
## TinyFS and sectors

- `ata_read_sector(lba) -> bool`: load one 512-byte sector into the shared filesystem buffer.
- `ata_write_sector(lba) -> bool`: write that buffer to one sector.
- `fs_buffer_get(index)` / `fs_buffer_set(index, value)`: byte access to the 512-byte buffer.
- `fs_buffer_clear()`, `fs_get_u32(offset)`, `fs_put_u32(offset, value)`: buffer helpers.

These are raw, global operations and currently have no extension permission gate. They can corrupt settings, ELF files, or user data. Third-party packages should use the namespaced KV API above and must not be considered fully sandboxed while raw ATA and physical-memory APIs remain globally callable.

The disk is 16MiB, but existing TinyFS regions still use fixed LBAs. Free capacity is not automatically allocated.

## ELF and raw hardware APIs

- `physical_read8(address)` / `physical_write8(address, value)`: raw physical memory access.
- `elf_call_entry(address)`: call a loaded ELF entry point.
- `io_in8`, `io_out8`, `io_in16`, `io_out16`: raw x86 port I/O.

`elf_image_size()` and `elf_image_get()` remain compatibility stubs and return no embedded ELF; programs are loaded from TinyFS.

These APIs are intentionally unsafe and bypass the settings permission model. Incorrect addresses, ports, or calling conventions can hang or corrupt the entire kernel. Use them only for hardware-boundary or loader extensions.

## Kernel-owned storage: do not use as extension scratch

`board_get/set` and `bag_get/set` expose Tetris engine arrays. They exist as LPython/llvmlite storage boundaries, not as stable extension APIs. Extensions should treat them as internal unless intentionally modifying live gameplay.

## Build

OS build:

```sh
docker compose run --rm osdev make
```

Standalone C ELF programs are separate:

```bat
extension\build_elf.bat
```

```sh
./extension/build_elf.sh
```

The extension directory is locally ignored by Git in this project, so explicitly revise `.gitignore` if an extension SDK or extension source should be published.