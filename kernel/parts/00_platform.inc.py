from lpython import i32, ccall

# All game policy is LPython. The linked functions are hardware/render edges.
@ccall
def vga_set_mode13() -> None:
    pass

@ccall
def vga_set_palette(mode: i32) -> None:
    pass

@ccall
def ui_put_cell(x: i32, y: i32, glyph: i32, colour: i32) -> None:
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
settings_generation: i32 = 0
settings_slot: i32 = 0
max_combo: i32 = 0
combo_generation: i32 = 0
combo_slot: i32 = 0
total_play_periods: i32 = 0
total_lines: i32 = 0
total_pieces: i32 = 0
stats_generation: i32 = 0
stats_slot: i32 = 0
stats_last_period: i32 = 0
system_periods: i32 = 0
music_index: i32 = 0
music_deadline: i32 = 0
music_note_off: i32 = 0
music_sounding: i32 = 0
music_playing: i32 = 0
bag_index: i32 = 7
last_bag_kind: i32 = -1
rng_state: i32 = 1

def keyboard_scancode() -> i32:
    while (io_in8(0x64) & 1) != 0:
        status: i32 = io_in8(0x64)
        code: i32 = io_in8(0x60)
        if (status & 0x20) == 0 and code != 0xE0 and code != 0xE1 and (code & 0x80) == 0:
            return code
    return 0

def pit_init() -> None:
    global pit_last, pit_periods, system_periods
    system_periods = 0
    divisor: i32 = 11932
    io_out8(0x43, 0x34)
    io_out8(0x40, divisor & 0xFF)
    io_out8(0x40, (divisor >> 8) & 0xFF)
    pit_periods = 0
    io_out8(0x43, 0)
    pit_last = io_in8(0x40) | (io_in8(0x40) << 8)

def pit_poll_elapsed(target_periods: i32) -> i32:
    global pit_last, pit_periods, move_cooldown_periods, system_periods
    io_out8(0x43, 0)
    current: i32 = io_in8(0x40) | (io_in8(0x40) << 8)
    if current > pit_last:
        system_periods = system_periods + 1
        pit_periods = pit_periods + 1
        if move_cooldown_periods > 0:
            move_cooldown_periods = move_cooldown_periods - 1
    pit_last = current
    if pit_periods >= target_periods:
        pit_periods = 0
        return 1
    return 0

def move_ready() -> bool:
    return move_cooldown_periods == 0

def arm_move_cooldown(periods: i32) -> None:
    global move_cooldown_periods
    move_cooldown_periods = periods

def pit_reset_elapsed() -> None:
    global pit_last, pit_periods
    pit_periods = 0
    io_out8(0x43, 0)
    pit_last = io_in8(0x40) | (io_in8(0x40) << 8)

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
    speaker_stop()

def music_update() -> None:
    global music_index, music_deadline, music_note_off, music_sounding
    if music_playing == 1 and music_sounding == 1 and system_periods >= music_note_off:
        speaker_stop()
        music_sounding = 0
    if music_playing == 1 and system_periods >= music_deadline:
        duration: i32 = korobeiniki_duration(music_index)
        note: i32 = korobeiniki_note(music_index)
        if note != 0 and bgm_volume > 0:
            speaker_start(note)
            music_sounding = 1
        else:
            speaker_stop()
            music_sounding = 0
        # A short gap between notes lowers perceived PC-speaker volume and
        # keeps the melody articulated instead of producing a solid square wave.
        music_note_off = system_periods + (duration * bgm_volume) // 10
        music_deadline = system_periods + duration
        music_index = (music_index + 1) % 35
def sound_tone(divisor: i32, duration: i32) -> None:
    if se_volume == 0:
        return
    sound_duration: i32 = (duration * se_volume + 9) // 10
    if sound_duration < 1:
        sound_duration = 1
    # PIT channel 2 drives the PC speaker; channel 0 remains the game clock.
    speaker: i32 = io_in8(0x61)
    io_out8(0x43, 0xB6)
    io_out8(0x42, divisor & 0xFF)
    io_out8(0x42, (divisor >> 8) & 0xFF)
    io_out8(0x61, speaker | 3)
    pit_reset_elapsed()
    while pit_poll_elapsed(sound_duration) == 0:
        pass
    io_out8(0x61, speaker & 0xFC)
    pit_reset_elapsed()

def sound_line_clear() -> None:
    sound_tone(1193, 2)
    sound_tone(796, 3)

def sound_game_over() -> None:
    sound_tone(1193, 3)
    sound_tone(1591, 3)
    sound_tone(2386, 5)
