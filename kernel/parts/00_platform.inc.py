from lpython import i32, ccall

keyboard_shifted: i32 = 0
keyboard_control: i32 = 0
keyboard_repeat_key: i32 = -1
keyboard_repeat_released: i32 = 1
keyboard_repeat_deadline: i32 = 0
boot_safe_mode: i32 = 0

# All game policy is LPython. The linked functions are hardware/render edges.
@ccall
def vga_set_mode13() -> None:
    pass

@ccall
@ccall
def ui_set_palette_entry(index: i32, red: i32, green: i32, blue: i32) -> None:
    pass
def vga_set_palette(mode: i32) -> None:
    pass

@ccall
def ui_native_plot(x: i32, y: i32, colour: i32) -> None:
    pass

@ccall
def ui_native_fill_rect(x: i32, y: i32, width: i32, height: i32, colour: i32) -> None:
    pass

@ccall
def ui_native_restore_surface() -> None:
    pass

@ccall
def ui_native_begin() -> None:
    pass

@ccall
def ui_native_end() -> None:
    pass

@ccall
def ui_native_blit_child(x: i32, y: i32) -> None:
    pass
@ccall
def ui_native_put_cell(x: i32, y: i32, glyph: i32, colour: i32) -> None:
    pass
@ccall
def ui_letterbox_fill_rect(x: i32, y: i32, width: i32, height: i32, colour: i32) -> None:
    pass

@ccall
def ui_letterbox_put_cell(x: i32, y: i32, glyph: i32, colour: i32) -> None:
    pass
@ccall
def ui_put_cell(x: i32, y: i32, glyph: i32, colour: i32) -> None:
    pass

@ccall
def ui_fill_rect(x: i32, y: i32, width: i32, height: i32, colour: i32) -> None:
    pass
@ccall
def ui_set_render_target(target: i32) -> None:
    pass

@ccall
@ccall
def ui_blit_window(x: i32, y: i32, width: i32, height: i32) -> None:
    pass
def ui_present_diff(reveal_x: i32) -> None:
    pass
@ccall
def elf_image_size() -> i32:
    pass

@ccall
def elf_image_get(index: i32) -> i32:
    pass

@ccall
def physical_write8(address: i32, value: i32) -> None:
    pass

@ccall
def physical_read8(address: i32) -> i32:
    pass

@ccall
def elf_call_entry(address: i32) -> i32:
    pass
@ccall
def io_in8(port: i32) -> i32:
    pass

@ccall
def io_out8(port: i32, value: i32) -> None:
    pass

@ccall
def io_in16(port: i32) -> i32:
    pass

@ccall
def io_out16(port: i32, value: i32) -> None:
    pass

@ccall
def any_note_get(index: i32) -> i32:
    pass

@ccall
def any_note_set(index: i32, value: i32) -> None:
    pass

@ccall
def any_name_get(index: i32) -> i32:
    pass

@ccall
def any_name_set(index: i32, value: i32) -> None:
    pass
@ccall
def extension_memory_get(index: i32) -> i32:
    pass

@ccall
def extension_memory_set(index: i32, value: i32) -> None:
    pass
@ccall
def fs_buffer_get(index: i32) -> i32:
    pass

@ccall
def fs_buffer_set(index: i32, value: i32) -> None:
    pass

@ccall
def board_get(index: i32) -> i32:
    pass

@ccall
def board_set(index: i32, value: i32) -> None:
    pass

@ccall
def bag_get(index: i32) -> i32:
    pass

@ccall
def bag_set(index: i32, value: i32) -> None:
    pass

pit_last: i32 = 0
pit_periods: i32 = 0
pit_subticks: i32 = 0
pit_reload: i32 = 11932
move_cooldown_periods: i32 = 0
high_score: i32 = 0
high_generation: i32 = 0
high_slot: i32 = 0
fs_ready: i32 = 0
color_mode: i32 = 0
gravity_periods: i32 = 50
control_mode: i32 = 0
bgm_volume: i32 = 6
se_volume: i32 = 5
debug_enabled: i32 = 1
clock_enabled: i32 = 1
ghost_enabled: i32 = 1
music_mode: i32 = 0
any_music_generation: i32 = 0
any_music_slot: i32 = 0
music_editor_note: i32 = 0
music_name_editing: i32 = 0
music_name_length: i32 = 3
settings_generation: i32 = 0
settings_slot: i32 = 0
# The generated registry sets these only while an extension callback runs.
extension_current_id: i32 = -1
extension_current_permissions: i32 = 0
extension_background_mask: i32 = 0
extension_notification_source: i32 = -1
extension_notification_length: i32 = 0
extension_notification_colour: i32 = 0x3F
extension_notification_until: i32 = 0
extension_notification_dirty: i32 = 0
extension_redraw_requested: i32 = 0
max_combo: i32 = 0
combo_generation: i32 = 0
combo_slot: i32 = 0
total_play_periods: i32 = 0
total_lines: i32 = 0
total_pieces: i32 = 0
stats_generation: i32 = 0
stats_slot: i32 = 0
stats_last_period: i32 = 0
achievements: i32 = 0
achievement_generation: i32 = 0
achievement_slot: i32 = 0
achievement_popup: i32 = -1
achievement_popup_until: i32 = 0
konami_progress: i32 = 0
achievement_page: i32 = 0
achievement_selection: i32 = 0
achievement_detail_open: i32 = 0
session_lines: i32 = 0
session_silent: i32 = 0
session_palette: i32 = 0
impossible_enabled: i32 = 0
game_start_rtc: i32 = 0
system_periods: i32 = 0
music_index: i32 = 0
music_deadline: i32 = 0
music_note_off: i32 = 0
music_sounding: i32 = 0
music_playing: i32 = 0
se_playing: i32 = 0
se_sounding: i32 = 0
se_index: i32 = 0
se_count: i32 = 0
se_deadline: i32 = 0
se_note_off: i32 = 0
se_music_remaining: i32 = 0
se_note_0: i32 = 0
se_note_1: i32 = 0
se_note_2: i32 = 0
se_duration_0: i32 = 0
se_duration_1: i32 = 0
se_duration_2: i32 = 0
bag_index: i32 = 7
last_bag_kind: i32 = -1
rng_state: i32 = 1

# Extension runtime capability helpers. The generated dispatcher supplies the
# current extension identity and restores it across nested calls.
def extension_request_redraw() -> None:
    global extension_redraw_requested
    extension_redraw_requested = 1

def extension_background_set(enabled: i32) -> i32:
    global extension_background_mask
    if extension_current_id < 0 or (extension_current_permissions & 16) == 0: return -1
    bit: i32 = 1 << extension_current_id
    if enabled != 0: extension_background_mask = extension_background_mask | bit
    else: extension_background_mask = extension_background_mask & (0 - bit - 1)
    return 0


def extension_notification_char_set(position: i32, character: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 64) == 0: return -1
    if position < 0 or position >= 16: return -2
    extension_memory_set(960 + position, character & 255)
    return 0


def extension_notification_show_text(message: str, colour: i32, duration: i32) -> i32:
    length: i32 = len(message)
    if length > 16: length = 16
    index: i32 = 0
    while index < length:
        if extension_notification_char_set(index, ord(message[index])) != 0: return -1
        index = index + 1
    return extension_notification_show(length, colour, duration)

def extension_notification_show(length: i32, colour: i32, duration: i32) -> i32:
    global extension_notification_source, extension_notification_length, extension_notification_colour, extension_notification_until, extension_notification_dirty
    if extension_current_id < 0 or (extension_current_permissions & 64) == 0: return -1
    if length < 0 or length > 16 or colour < 0 or colour > 255: return -2
    display_duration: i32 = duration
    if display_duration < 1: display_duration = 1
    if display_duration > 3000: display_duration = 3000
    index: i32 = 0
    while index < length:
        extension_memory_set(976 + index, extension_memory_get(960 + index))
        index = index + 1
    extension_notification_source = extension_current_id
    extension_notification_length = length
    extension_notification_colour = colour
    extension_notification_until = system_periods + display_duration
    extension_notification_dirty = 1
    return 0

def extension_find(name: str) -> i32:
    wanted_length: i32 = len(name)
    identifier: i32 = 0
    while identifier < extension_count():
        same: bool = extension_name_length(identifier) == wanted_length
        position: i32 = 0
        while same and position < wanted_length:
            character: i32 = ord(name[position])
            if character >= 97 and character <= 122: character = character - 32
            if extension_name_char(identifier, position) != character: same = False
            position = position + 1
        if same: return identifier
        identifier = identifier + 1
    return -1


def extension_send_message_named(name: str, topic: i32, value: i32) -> i32:
    target: i32 = extension_find(name)
    if target < 0: return -2
    return extension_send_message(target, topic, value)


def extension_now_ms() -> i32:
    return system_periods * 10


def extension_mouse_buttons(packet: i32) -> i32:
    return packet & 7


def extension_mouse_dx(packet: i32) -> i32:
    value: i32 = (packet >> 8) & 255
    return value - 256 if value >= 128 else value


def extension_mouse_dy(packet: i32) -> i32:
    value: i32 = (packet >> 16) & 255
    return value - 256 if value >= 128 else value


def extension_play_pitch(pitch: i32, duration: i32) -> None:
    sound_tone(pitch_divisor(pitch), duration)

def rtc_read(register: i32) -> i32:
    io_out8(0x70, register)
    return io_in8(0x71)

def bcd_value(value: i32) -> i32:
    return (value & 15) + ((value >> 4) & 15) * 10

def rtc_seconds_of_day() -> i32:
    attempts: i32 = 0
    while (rtc_read(0x0A) & 0x80) != 0 and attempts < 1000:
        attempts = attempts + 1
    second: i32 = rtc_read(0)
    minute: i32 = rtc_read(2)
    hour: i32 = rtc_read(4)
    status_b: i32 = rtc_read(0x0B)
    if (status_b & 4) == 0:
        second = bcd_value(second)
        minute = bcd_value(minute)
        hour = bcd_value(hour & 0x7F)
    return hour * 3600 + minute * 60 + second
def keyboard_scancode() -> i32:
    global keyboard_shifted, keyboard_control, keyboard_repeat_key, keyboard_repeat_released, keyboard_repeat_deadline
    while (io_in8(0x64) & 1) != 0:
        status: i32 = io_in8(0x64)
        code: i32 = io_in8(0x60)
        if (status & 0x20) == 0 and code != 0xE0 and code != 0xE1:
            if code == 0x2A or code == 0x36:
                if keyboard_shifted == 0:
                    keyboard_shifted = 1
                    return code
            elif code == 0x1D:
                keyboard_control = 1
            elif code == 0x9D:
                keyboard_control = 0
            elif code == 0xAA or code == 0xB6:
                keyboard_shifted = 0
            elif (code & 0x80) != 0:
                released_code: i32 = code & 0x7F
                if released_code == keyboard_repeat_key:
                    keyboard_repeat_released = 1
            else:
                if code != keyboard_repeat_key or keyboard_repeat_released == 1:
                    keyboard_repeat_key = code
                    keyboard_repeat_released = 0
                    keyboard_repeat_deadline = system_periods + 30
                    return code
                if system_periods >= keyboard_repeat_deadline:
                    keyboard_repeat_deadline = system_periods + 6
                    return code
    return 0

ps2_mouse_phase: i32 = 0
ps2_mouse_first: i32 = 0
ps2_mouse_second: i32 = 0


def ps2_wait_write() -> None:
    attempts: i32 = 0
    while (io_in8(0x64) & 2) != 0 and attempts < 100000:
        attempts = attempts + 1


def ps2_wait_read() -> i32:
    attempts: i32 = 0
    while (io_in8(0x64) & 1) == 0 and attempts < 100000:
        attempts = attempts + 1
    if attempts >= 100000: return -1
    return io_in8(0x60)


def ps2_mouse_command(command: i32) -> None:
    ps2_wait_write(); io_out8(0x64, 0xD4)
    ps2_wait_write(); io_out8(0x60, command)
    ps2_wait_read()


def ps2_mouse_init() -> None:
    global ps2_mouse_phase
    ps2_mouse_phase = 0
    ps2_wait_write(); io_out8(0x64, 0xA8)
    ps2_wait_write(); io_out8(0x64, 0x20)
    command_byte: i32 = ps2_wait_read()
    if command_byte < 0: command_byte = 0
    command_byte = (command_byte | 2) & 0xDF
    ps2_wait_write(); io_out8(0x64, 0x60)
    ps2_wait_write(); io_out8(0x60, command_byte)
    ps2_mouse_command(0xF6)
    ps2_mouse_command(0xF4)


def ps2_mouse_poll() -> i32:
    global ps2_mouse_phase, ps2_mouse_first, ps2_mouse_second
    while (io_in8(0x64) & 0x21) == 0x21:
        data: i32 = io_in8(0x60)
        if ps2_mouse_phase == 0:
            if (data & 8) != 0:
                ps2_mouse_first = data
                ps2_mouse_phase = 1
        elif ps2_mouse_phase == 1:
            ps2_mouse_second = data
            ps2_mouse_phase = 2
        else:
            ps2_mouse_phase = 0
            if (ps2_mouse_first & 0xC0) == 0:
                return -2147483648 | (ps2_mouse_first & 7) | ((ps2_mouse_second & 255) << 8) | ((data & 255) << 16)
    return 0

def pit_latch_current() -> i32:
    io_out8(0x43, 0)
    return io_in8(0x40) | (io_in8(0x40) << 8)

def pit_init() -> None:
    global pit_last, pit_periods, pit_subticks, system_periods
    system_periods = 0
    pit_periods = 0
    pit_subticks = 0
    io_out8(0x43, 0x34)
    io_out8(0x40, pit_reload & 0xFF)
    io_out8(0x40, (pit_reload >> 8) & 0xFF)
    pit_last = pit_latch_current()

def pit_update_clock() -> None:
    global pit_last, pit_periods, pit_subticks, move_cooldown_periods, system_periods
    current: i32 = pit_latch_current()
    delta: i32 = pit_last - current if current <= pit_last else pit_last + pit_reload - current
    pit_last = current
    pit_subticks = pit_subticks + delta
    elapsed: i32 = 0
    while pit_subticks >= pit_reload:
        pit_subticks = pit_subticks - pit_reload
        elapsed = elapsed + 1
    if elapsed > 0:
        system_periods = system_periods + elapsed
        pit_periods = pit_periods + elapsed
        if move_cooldown_periods > elapsed:
            move_cooldown_periods = move_cooldown_periods - elapsed
        else:
            move_cooldown_periods = 0

def pit_poll_elapsed(target_periods: i32) -> i32:
    global pit_periods
    pit_update_clock()
    if pit_periods >= target_periods:
        pit_periods = pit_periods - target_periods
        return 1
    return 0
def move_ready() -> bool:
    return move_cooldown_periods == 0

def arm_move_cooldown(periods: i32) -> None:
    global move_cooldown_periods
    move_cooldown_periods = periods

def pit_reset_elapsed() -> None:
    global pit_periods
    pit_update_clock()
    pit_periods = 0

def speaker_start(divisor: i32) -> None:
    speaker: i32 = io_in8(0x61)
    if divisor == 0:
        io_out8(0x61, speaker & 0xFC)
        return
    io_out8(0x43, 0xB6)
    io_out8(0x42, divisor & 0xFF)
    io_out8(0x42, (divisor >> 8) & 0xFF)
    io_out8(0x61, speaker | 3)

def speaker_stop() -> None:
    io_out8(0x61, io_in8(0x61) & 0xFC)

def korobeiniki_note(index: i32) -> i32:
    # Public-domain 1861 Korobeiniki score, converted from staff pitch to
    # 1,193,182 Hz PIT divisors (nearest integer).
    step: i32 = index % 35
    if step == 0 or step == 4: return 1810       # E5
    if step == 1 or step == 3: return 1436       # G-sharp5
    if step == 2 or step == 10 or step == 27: return 1208  # B5
    if step == 5 or step == 15 or step == 16 or step == 32 or step == 33: return 1356  # A5
    if step == 6 or step == 9 or step == 11 or step == 14 or step == 26 or step == 28 or step == 31: return 1140  # C6
    if step == 7 or step == 13 or step == 22 or step == 24 or step == 30: return 905   # E6
    if step == 8 or step == 12 or step == 25 or step == 29: return 1016  # D6
    if step == 17 or step == 21 or step == 23: return 854   # F6
    if step == 18 or step == 20: return 761                 # G6
    if step == 19: return 678                               # A6
    return 0

def korobeiniki_duration(index: i32) -> i32:
    # One unit is a 10 ms PIT period. Eighth=200 ms at roughly 150 BPM.
    step: i32 = index % 35
    if step == 0 or step == 5 or step == 10 or step == 17 or step == 22 or step == 27:
        return 60   # dotted quarter
    if step == 16 or step == 33:
        return 80   # half note
    if step == 1 or step == 3 or step == 4 or step == 6 or step == 8 or step == 9 or step == 11 or step == 18 or step == 20 or step == 21 or step == 23 or step == 25 or step == 26 or step == 28:
        return 20   # eighth note
    if step == 34:
        return 40   # phrase rest
    return 40       # quarter note
def kalinka_note(index: i32) -> i32:
    # Refrain transcribed from the public-domain Larionov score (E minor, 2/4).
    step: i32 = index % 23
    if step == 0 or step == 12 or step == 13: return 1208  # B5
    if step == 1 or step == 4 or step == 7 or step == 14 or step == 18 or step == 21: return 1356  # A5
    if step == 2 or step == 5 or step == 9 or step == 16 or step == 19 or step == 22: return 1612  # F#5
    if step == 3 or step == 6 or step == 8 or step == 15 or step == 17 or step == 20: return 1522  # G5
    return 1810  # E5

def kalinka_duration(index: i32) -> i32:
    step: i32 = index % 23
    if step == 0 or step == 1 or step == 4 or step == 7 or step == 11 or step == 18 or step == 21: return 40
    if step == 14: return 30
    if step == 15: return 10
    return 20
def pitch_divisor(pitch: i32) -> i32:
    if pitch == 0: return 1810
    if pitch == 1: return 1612
    if pitch == 2: return 1436
    if pitch == 3: return 1356
    if pitch == 4: return 1208
    if pitch == 5: return 1140
    if pitch == 6: return 1016
    if pitch == 7: return 905
    if pitch == 8: return 854
    return 761

def divisor_pitch(divisor: i32) -> i32:
    pitch: i32 = 0
    best_pitch: i32 = 0
    best_distance: i32 = 100000
    while pitch < 10:
        distance: i32 = pitch_divisor(pitch) - divisor
        if distance < 0: distance = -distance
        if distance < best_distance:
            best_distance = distance
            best_pitch = pitch
        pitch = pitch + 1
    return best_pitch

def any_music_reset() -> None:
    global music_name_length
    index: i32 = 0
    while index < 32:
        any_note_set(index, korobeiniki_note(index) | (korobeiniki_duration(index) << 16))
        index = index + 1
    any_name_set(0, 65); any_name_set(1, 78); any_name_set(2, 89)
    index = 3
    while index < 8:
        any_name_set(index, 0)
        index = index + 1
    music_name_length = 3
def music_start() -> None:
    global music_index, music_deadline, music_note_off, music_sounding, music_playing
    music_index = 0
    music_deadline = system_periods
    music_note_off = system_periods
    music_sounding = 0
    music_playing = 1

def music_stop() -> None:
    global music_playing, music_sounding
    music_playing = 0
    music_sounding = 0
    if se_playing == 0: speaker_stop()

def music_update() -> None:
    global music_index, music_deadline, music_note_off, music_sounding
    # Channel 2 belongs exclusively to SE while an effect is active.
    if se_playing != 0:
        return
    if music_playing == 1 and music_sounding == 1 and system_periods >= music_note_off:
        speaker_stop()
        music_sounding = 0
    if music_playing == 1 and system_periods >= music_deadline:
        duration: i32 = 0
        note: i32 = 0
        music_length: i32 = 35
        if music_mode == 2:
            packed_note: i32 = any_note_get(music_index % 32)
            note = packed_note & 0xFFFF
            duration = (packed_note >> 16) & 0xFFFF
            if (duration & 0x8000) != 0:
                note = 0
                duration = duration & 0x7FFF
            music_length = 32
        elif music_mode == 1:
            note = kalinka_note(music_index)
            duration = kalinka_duration(music_index)
            music_length = 23
        else:
            duration = korobeiniki_duration(music_index)
            note = korobeiniki_note(music_index)
        if note != 0 and bgm_volume > 0:
            speaker_start(note)
            music_sounding = 1
        else:
            speaker_stop()
            music_sounding = 0
        music_note_off = system_periods + (duration * bgm_volume) // 10
        music_deadline = system_periods + duration
        music_index = (music_index + 1) % music_length

def se_note(index: i32) -> i32:
    if index == 0: return se_note_0
    if index == 1: return se_note_1
    return se_note_2

def se_duration(index: i32) -> i32:
    if index == 0: return se_duration_0
    if index == 1: return se_duration_1
    return se_duration_2

def sound_begin_slot() -> None:
    global se_deadline, se_note_off, se_sounding, music_sounding
    duration: i32 = se_duration(se_index)
    note: i32 = se_note(se_index)
    music_sounding = 0
    if note != 0 and se_volume > 0:
        speaker_start(note)
        se_sounding = 1
    else:
        speaker_stop()
        se_sounding = 0
    se_note_off = system_periods + (duration * se_volume) // 10
    se_deadline = system_periods + duration

def sound_sequence(note0: i32, duration0: i32, note1: i32, duration1: i32, note2: i32, duration2: i32, count: i32) -> None:
    global se_note_0, se_note_1, se_note_2, se_duration_0, se_duration_1, se_duration_2, se_index, se_count, se_playing, se_music_remaining
    if se_volume == 0:
        return
    if se_playing == 0:
        se_music_remaining = music_deadline - system_periods if music_deadline > system_periods else 0
    se_note_0 = note0
    se_note_1 = note1
    se_note_2 = note2
    se_duration_0 = duration0
    se_duration_1 = duration1
    se_duration_2 = duration2
    se_index = 0
    se_count = count
    se_playing = 1
    sound_begin_slot()

def sound_update() -> None:
    global se_index, se_playing, se_sounding, music_deadline
    if se_playing == 0:
        return
    if se_sounding == 1 and system_periods >= se_note_off:
        speaker_stop()
        se_sounding = 0
    if system_periods >= se_deadline:
        se_index = se_index + 1
        if se_index >= se_count:
            se_playing = 0
            se_sounding = 0
            speaker_stop()
            # Preserve the musical clock: SE pauses the remaining interval
            # instead of forcing the next BGM note to start early.
            music_deadline = system_periods + se_music_remaining
        else:
            sound_begin_slot()

def sound_tone(divisor: i32, duration: i32) -> None:
    sound_sequence(divisor, duration, 0, 0, 0, 0, 1)

def sound_line_clear() -> None:
    sound_sequence(1193, 2, 796, 3, 0, 0, 2)

def sound_game_over() -> None:
    sound_sequence(1193, 3, 1591, 3, 2386, 5, 3)