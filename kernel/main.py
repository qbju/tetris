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

pit_last: i32 = 0
pit_periods: i32 = 0
move_cooldown_periods: i32 = 0
high_score: i32 = 0
high_generation: i32 = 0
high_slot: i32 = 0
fs_ready: i32 = 0
color_mode: i32 = 0
gravity_periods: i32 = 50
settings_generation: i32 = 0
settings_slot: i32 = 0

def keyboard_scancode() -> i32:
    while (io_in8(0x64) & 1) != 0:
        status: i32 = io_in8(0x64)
        code: i32 = io_in8(0x60)
        if (status & 0x20) == 0 and code != 0xE0 and code != 0xE1 and (code & 0x80) == 0:
            return code
    return 0

def pit_init() -> None:
    global pit_last, pit_periods
    divisor: i32 = 11932
    io_out8(0x43, 0x34)
    io_out8(0x40, divisor & 0xFF)
    io_out8(0x40, (divisor >> 8) & 0xFF)
    pit_periods = 0
    io_out8(0x43, 0)
    pit_last = io_in8(0x40) | (io_in8(0x40) << 8)

def pit_poll_elapsed(target_periods: i32) -> i32:
    global pit_last, pit_periods, move_cooldown_periods
    io_out8(0x43, 0)
    current: i32 = io_in8(0x40) | (io_in8(0x40) << 8)
    if current > pit_last:
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

# TinyFS uses a writable primary-master IDE disk. Sector 0 is the superblock,
# sector 1 is a directory, and sector 8 stores two atomic high-score records.
def fs_buffer_clear() -> None:
    index: i32 = 0
    while index < 512:
        fs_buffer_set(index, 0)
        index = index + 1


def fs_put_u32(offset: i32, value: i32) -> None:
    fs_buffer_set(offset, value & 255)
    fs_buffer_set(offset + 1, (value >> 8) & 255)
    fs_buffer_set(offset + 2, (value >> 16) & 255)
    fs_buffer_set(offset + 3, (value >> 24) & 255)


def fs_get_u32(offset: i32) -> i32:
    return fs_buffer_get(offset) | (fs_buffer_get(offset + 1) << 8) | (fs_buffer_get(offset + 2) << 16) | (fs_buffer_get(offset + 3) << 24)


def ata_wait_drq() -> bool:
    attempts: i32 = 0
    while attempts < 200000:
        status: i32 = io_in8(0x1F7)
        if (status & 1) != 0:
            return False
        if (status & 0x80) == 0 and (status & 8) != 0:
            return True
        attempts = attempts + 1
    return False


def ata_select_sector(lba: i32) -> None:
    # 0xE0 selects the primary master, where QEMU attaches data.img.
    io_out8(0x1F6, 0xE0 | ((lba >> 24) & 15))
    io_out8(0x1F2, 1)
    io_out8(0x1F3, lba & 255)
    io_out8(0x1F4, (lba >> 8) & 255)
    io_out8(0x1F5, (lba >> 16) & 255)


def ata_read_sector(lba: i32) -> bool:
    ata_select_sector(lba)
    io_out8(0x1F7, 0x20)
    if not ata_wait_drq():
        return False
    word_index: i32 = 0
    while word_index < 256:
        word: i32 = io_in16(0x1F0)
        fs_buffer_set(word_index * 2, word & 255)
        fs_buffer_set(word_index * 2 + 1, (word >> 8) & 255)
        word_index = word_index + 1
    return True


def ata_write_sector(lba: i32) -> bool:
    ata_select_sector(lba)
    io_out8(0x1F7, 0x30)
    if not ata_wait_drq():
        return False
    word_index: i32 = 0
    while word_index < 256:
        word: i32 = fs_buffer_get(word_index * 2) | (fs_buffer_get(word_index * 2 + 1) << 8)
        io_out16(0x1F0, word)
        word_index = word_index + 1
    io_out8(0x1F7, 0xE7)
    attempts: i32 = 0
    while attempts < 200000:
        status: i32 = io_in8(0x1F7)
        if (status & 1) != 0:
            return False
        if (status & 0x80) == 0:
            return True
        attempts = attempts + 1
    return False


def fs_format() -> bool:
    # Superblock: magic PYFS, version, block size, directory/data locations.
    fs_buffer_clear()
    fs_buffer_set(0, 80); fs_buffer_set(1, 89); fs_buffer_set(2, 70); fs_buffer_set(3, 83)
    fs_put_u32(4, 1); fs_put_u32(8, 512); fs_put_u32(12, 1); fs_put_u32(16, 8)
    if not ata_write_sector(0):
        return False
    # One fixed-size root entry named HIGHSCORE, backed by sector 8.
    fs_buffer_clear()
    fs_buffer_set(0, 68); fs_buffer_set(1, 73); fs_buffer_set(2, 82); fs_buffer_set(3, 49)
    fs_buffer_set(32, 72); fs_buffer_set(33, 73); fs_buffer_set(34, 71); fs_buffer_set(35, 72)
    fs_buffer_set(36, 83); fs_buffer_set(37, 67); fs_buffer_set(38, 79); fs_buffer_set(39, 82); fs_buffer_set(40, 69)
    fs_put_u32(48, 8); fs_put_u32(52, 32)
    # Second root entry: SETTINGS, backed by sector 9.
    fs_buffer_set(64, 83); fs_buffer_set(65, 69); fs_buffer_set(66, 84); fs_buffer_set(67, 84)
    fs_buffer_set(68, 73); fs_buffer_set(69, 78); fs_buffer_set(70, 71); fs_buffer_set(71, 83)
    fs_put_u32(80, 9); fs_put_u32(84, 48)
    if not ata_write_sector(1):
        return False
    fs_buffer_clear()
    if not ata_write_sector(8):
        return False
    fs_buffer_clear()
    return ata_write_sector(9)


def score_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 72 or fs_buffer_get(offset + 1) != 83:
        return False
    generation: i32 = fs_get_u32(offset + 4)
    saved_score: i32 = fs_get_u32(offset + 8)
    return fs_get_u32(offset + 12) == (generation ^ saved_score ^ 0x50594653)


def fs_load_high_score() -> None:
    global high_score, high_generation, high_slot
    high_score = 0
    high_generation = 0
    high_slot = 0
    if not ata_read_sector(8):
        return
    valid_a: bool = score_record_valid(0)
    valid_b: bool = score_record_valid(16)
    generation_a: i32 = fs_get_u32(4) if valid_a else -1
    generation_b: i32 = fs_get_u32(20) if valid_b else -1
    if valid_b and generation_b > generation_a:
        high_slot = 1
        high_generation = generation_b
        high_score = fs_get_u32(24)
    elif valid_a:
        high_slot = 0
        high_generation = generation_a
        high_score = fs_get_u32(8)


def fs_ensure_settings_entry() -> None:
    if not ata_read_sector(1):
        return
    valid: bool = fs_buffer_get(64) == 83 and fs_buffer_get(65) == 69 and fs_buffer_get(66) == 84 and fs_buffer_get(67) == 84
    if valid:
        return
    fs_buffer_set(64, 83); fs_buffer_set(65, 69); fs_buffer_set(66, 84); fs_buffer_set(67, 84)
    fs_buffer_set(68, 73); fs_buffer_set(69, 78); fs_buffer_set(70, 71); fs_buffer_set(71, 83)
    fs_put_u32(80, 9); fs_put_u32(84, 48)
    ata_write_sector(1)


def settings_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 83 or fs_buffer_get(offset + 1) != 84:
        return False
    generation: i32 = fs_get_u32(offset + 4)
    saved_colour: i32 = fs_get_u32(offset + 8)
    saved_gravity: i32 = fs_get_u32(offset + 12)
    checksum: i32 = generation ^ saved_colour ^ saved_gravity ^ 0x53545447
    return fs_get_u32(offset + 16) == checksum and saved_colour >= 0 and saved_colour <= 2 and saved_gravity >= 10 and saved_gravity <= 100


def fs_load_settings() -> None:
    global color_mode, gravity_periods, settings_generation, settings_slot
    color_mode = 0
    gravity_periods = 50
    settings_generation = 0
    settings_slot = 0
    if not ata_read_sector(9):
        return
    valid_a: bool = settings_record_valid(0)
    valid_b: bool = settings_record_valid(24)
    generation_a: i32 = fs_get_u32(4) if valid_a else -1
    generation_b: i32 = fs_get_u32(28) if valid_b else -1
    offset: i32 = 0
    if valid_b and generation_b > generation_a:
        settings_slot = 1
        settings_generation = generation_b
        offset = 24
    elif valid_a:
        settings_slot = 0
        settings_generation = generation_a
    else:
        return
    color_mode = fs_get_u32(offset + 8)
    gravity_periods = fs_get_u32(offset + 12)


def fs_save_settings() -> None:
    global settings_generation, settings_slot
    if fs_ready == 0:
        return
    if not ata_read_sector(9):
        return
    new_slot: i32 = 0 if settings_slot == 1 else 1
    offset: i32 = new_slot * 24
    generation: i32 = settings_generation + 1
    fs_buffer_set(offset, 83); fs_buffer_set(offset + 1, 84)
    fs_buffer_set(offset + 2, 1); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation)
    fs_put_u32(offset + 8, color_mode)
    fs_put_u32(offset + 12, gravity_periods)
    fs_put_u32(offset + 16, generation ^ color_mode ^ gravity_periods ^ 0x53545447)
    fs_put_u32(offset + 20, 0)
    if ata_write_sector(9):
        settings_generation = generation
        settings_slot = new_slot


def fs_reset_data() -> None:
    global high_score, high_generation, high_slot, color_mode, gravity_periods, settings_generation, settings_slot
    high_score = 0
    high_generation = 0
    high_slot = 0
    color_mode = 0
    gravity_periods = 50
    settings_generation = 0
    settings_slot = 0
    if fs_ready == 0:
        return
    fs_buffer_clear()
    ata_write_sector(8)
    fs_buffer_clear()
    ata_write_sector(9)

def fs_mount() -> None:
    global fs_ready
    fs_ready = 0
    if not ata_read_sector(0):
        return
    valid: bool = fs_buffer_get(0) == 80 and fs_buffer_get(1) == 89 and fs_buffer_get(2) == 70 and fs_buffer_get(3) == 83
    if not valid:
        if not fs_format():
            return
    fs_ready = 1
    fs_ensure_settings_entry()
    fs_load_high_score()
    fs_load_settings()


def fs_save_high_score(value: i32) -> None:
    global high_score, high_generation, high_slot
    if fs_ready == 0 or value <= high_score:
        return
    if not ata_read_sector(8):
        return
    new_slot: i32 = 0 if high_slot == 1 else 1
    offset: i32 = new_slot * 16
    generation: i32 = high_generation + 1
    fs_buffer_set(offset, 72); fs_buffer_set(offset + 1, 83)
    fs_buffer_set(offset + 2, 1); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation)
    fs_put_u32(offset + 8, value)
    fs_put_u32(offset + 12, generation ^ value ^ 0x50594653)
    if ata_write_sector(8):
        high_score = value
        high_generation = generation
        high_slot = new_slot

# 10x24 storage: rows -4..-1 are hidden, rows 0..19 are visible.
# Storage is provided by llvmlite because LPython does not initialise a
# descriptor for a module-level fixed-size array.
kind: i32 = 0
rotation: i32 = 0
piece_x: i32 = 3
piece_y: i32 = 0
next_kind: i32 = 1
score: i32 = 0
ticks: i32 = 0
game_over: i32 = 0
key_cooldown: i32 = 0
started: i32 = 0
last_key: i32 = 0
menu_drawn: i32 = 0
menu_page: i32 = 0
menu_selection: i32 = 0
settings_selection: i32 = 0
reset_choice: i32 = 1
held_kind: i32 = -1
hold_used: i32 = 0
grounded: i32 = 0
game_initialized: i32 = 0
game_over_drawn: i32 = 0
merge_count: i32 = 0
debug_filled: i32 = -1
debug_started: i32 = -1
debug_game_over: i32 = -1
debug_grounded: i32 = -1
debug_piece_y: i32 = -100
debug_merge_count: i32 = -1
debug_banner_drawn: i32 = 0
debug_visible: i32 = 0

def text(x: i32, y: i32, value: i32, colour: i32) -> None:
    # A foreground-only colour inherits the UI's navy background instead of
    # punching a black rectangle around every glyph.
    attribute: i32 = colour
    if colour < 0x10:
        attribute = colour | 0x10
    ui_put_cell(x, y, value, attribute)

def hex_digit(value: i32) -> i32:
    if value < 10:
        return 48 + value
    return 55 + value

def put_hex8(value: i32, x: i32, y: i32) -> None:
    text(x, y, hex_digit((value >> 4) & 15), 0x0E)
    text(x + 1, y, hex_digit(value & 15), 0x0E)

def clear_screen(colour: i32) -> None:
    y: i32 = 0
    while y < 25:
        x: i32 = 0
        while x < 80:
            ui_put_cell(x, y, 32, colour)
            x = x + 1
        y = y + 1

def draw_menu_shell(title_kind: i32) -> None:
    clear_screen(0x10)
    x: i32 = 0
    while x < 80:
        ui_put_cell(x, 0, 32, 0x51)
        ui_put_cell(x, 1, 32, 0x51)
        ui_put_cell(x, 23, 32, 0x14)
        ui_put_cell(x, 24, 32, 0x14)
        x = x + 1
    x = 18
    while x < 62:
        ui_put_cell(x, 3, 205, 0x1B)
        ui_put_cell(x, 21, 205, 0x1B)
        x = x + 1
    y: i32 = 4
    while y < 21:
        ui_put_cell(18, y, 186, 0x1B)
        ui_put_cell(61, y, 186, 0x1B)
        y = y + 1
    text(18, 3, 201, 0x1B); text(61, 3, 187, 0x1B)
    text(18, 21, 200, 0x1B); text(61, 21, 188, 0x1B)
    if title_kind == 0:
        text(34, 4, 84, 0x0E); text(35, 4, 69, 0x0E); text(36, 4, 84, 0x0E)
        text(37, 4, 82, 0x0E); text(38, 4, 73, 0x0E); text(39, 4, 83, 0x0E)
        text(41, 4, 79, 0x0B); text(42, 4, 83, 0x0B)
    else:
        text(35, 4, 83, 0x0E); text(36, 4, 69, 0x0E); text(37, 4, 84, 0x0E)
        text(38, 4, 84, 0x0E); text(39, 4, 73, 0x0E); text(40, 4, 78, 0x0E)
        text(41, 4, 71, 0x0E); text(42, 4, 83, 0x0E)


def draw_menu_button(item: i32, y: i32) -> None:
    selected: i32 = 1 if menu_selection == item else 0
    top_colour: i32 = 0x3B if selected == 1 else 0x1B
    middle_colour: i32 = 0x2A if selected == 1 else 0x18
    x: i32 = 27
    while x < 53:
        ui_put_cell(x, y, 32, top_colour)
        ui_put_cell(x, y + 1, 32, middle_colour)
        ui_put_cell(x, y + 2, 32, top_colour)
        x = x + 1
    if selected == 1:
        text(29, y + 1, 16, 0x2E)


def draw_menu() -> None:
    draw_menu_shell(0)
    draw_menu_button(0, 6)
    draw_menu_button(1, 10)
    draw_menu_button(2, 14)
    text(37, 7, 80, 0x2F if menu_selection == 0 else 0x1F)
    text(38, 7, 76, 0x2F if menu_selection == 0 else 0x1F)
    text(39, 7, 65, 0x2F if menu_selection == 0 else 0x1F)
    text(40, 7, 89, 0x2F if menu_selection == 0 else 0x1F)
    text(35, 11, 83, 0x2F if menu_selection == 1 else 0x1F)
    text(36, 11, 69, 0x2F if menu_selection == 1 else 0x1F)
    text(37, 11, 84, 0x2F if menu_selection == 1 else 0x1F)
    text(38, 11, 84, 0x2F if menu_selection == 1 else 0x1F)
    text(39, 11, 73, 0x2F if menu_selection == 1 else 0x1F)
    text(40, 11, 78, 0x2F if menu_selection == 1 else 0x1F)
    text(41, 11, 71, 0x2F if menu_selection == 1 else 0x1F)
    text(42, 11, 83, 0x2F if menu_selection == 1 else 0x1F)
    text(34, 15, 82, 0x2F if menu_selection == 2 else 0x1F)
    text(35, 15, 69, 0x2F if menu_selection == 2 else 0x1F)
    text(36, 15, 83, 0x2F if menu_selection == 2 else 0x1F)
    text(37, 15, 69, 0x2F if menu_selection == 2 else 0x1F)
    text(38, 15, 84, 0x2F if menu_selection == 2 else 0x1F)
    text(40, 15, 68, 0x2F if menu_selection == 2 else 0x1F)
    text(41, 15, 65, 0x2F if menu_selection == 2 else 0x1F)
    text(42, 15, 84, 0x2F if menu_selection == 2 else 0x1F)
    text(43, 15, 65, 0x2F if menu_selection == 2 else 0x1F)
    text(32, 19, 85, 0x07); text(33, 19, 80, 0x07)
    text(35, 19, 68, 0x07); text(36, 19, 79, 0x07); text(37, 19, 87, 0x07); text(38, 19, 78, 0x07)
    text(40, 19, 69, 0x07); text(41, 19, 78, 0x07); text(42, 19, 84, 0x07); text(43, 19, 69, 0x07); text(44, 19, 82, 0x07)
    if debug_visible == 1:
        put_hex8(last_key, 48, 19)


def draw_settings() -> None:
    draw_menu_shell(1)
    cursor_y: i32 = 8 if settings_selection == 0 else (12 if settings_selection == 1 else 17)
    text(21, cursor_y, 16, 0x0E)
    text(24, 8, 67, 0x0B); text(25, 8, 79, 0x0B); text(26, 8, 76, 0x0B)
    text(27, 8, 79, 0x0B); text(28, 8, 82, 0x0B)
    if color_mode == 0:
        text(43, 8, 78, 0x0F); text(44, 8, 79, 0x0F); text(45, 8, 82, 0x0F)
        text(46, 8, 77, 0x0F); text(47, 8, 65, 0x0F); text(48, 8, 76, 0x0F)
    elif color_mode == 1:
        text(40, 8, 71, 0x0F); text(41, 8, 82, 0x0F); text(42, 8, 65, 0x0F)
        text(43, 8, 89, 0x0F); text(44, 8, 83, 0x0F); text(45, 8, 67, 0x0F)
        text(46, 8, 65, 0x0F); text(47, 8, 76, 0x0F); text(48, 8, 69, 0x0F)
    else:
        text(41, 8, 73, 0x0F); text(42, 8, 78, 0x0F); text(43, 8, 86, 0x0F)
        text(44, 8, 69, 0x0F); text(45, 8, 82, 0x0F); text(46, 8, 84, 0x0F)
        text(47, 8, 69, 0x0F); text(48, 8, 68, 0x0F)
    text(24, 12, 71, 0x0B); text(25, 12, 82, 0x0B); text(26, 12, 65, 0x0B)
    text(27, 12, 86, 0x0B); text(28, 12, 73, 0x0B); text(29, 12, 84, 0x0B); text(30, 12, 89, 0x0B)
    put_number(gravity_periods * 10, 42, 12)
    text(48, 12, 77, 0x07); text(49, 12, 83, 0x07)
    text(34, 17, 83, 0x0A); text(35, 17, 65, 0x0A); text(36, 17, 86, 0x0A); text(37, 17, 69, 0x0A)
    text(39, 17, 66, 0x0A); text(40, 17, 65, 0x0A); text(41, 17, 67, 0x0A); text(42, 17, 75, 0x0A)
    text(28, 19, 76, 0x07); text(29, 19, 69, 0x07); text(30, 19, 70, 0x07); text(31, 19, 84, 0x07)
    text(33, 19, 82, 0x07); text(34, 19, 73, 0x07); text(35, 19, 71, 0x07); text(36, 19, 72, 0x07); text(37, 19, 84, 0x07)


def draw_reset_dialog() -> None:
    draw_menu()
    y: i32 = 7
    while y < 19:
        x: i32 = 20
        while x < 60:
            ui_put_cell(x, y, 32, 0x50)
            x = x + 1
        y = y + 1
    x = 20
    while x < 60:
        ui_put_cell(x, 7, 205, 0x5F); ui_put_cell(x, 18, 205, 0x5F)
        x = x + 1
    y = 8
    while y < 18:
        ui_put_cell(20, y, 186, 0x5F); ui_put_cell(59, y, 186, 0x5F)
        y = y + 1
    text(20, 7, 201, 0x5F); text(59, 7, 187, 0x5F)
    text(20, 18, 200, 0x5F); text(59, 18, 188, 0x5F)
    text(34, 9, 82, 0x5F); text(35, 9, 69, 0x5F); text(36, 9, 83, 0x5F)
    text(37, 9, 69, 0x5F); text(38, 9, 84, 0x5F)
    text(40, 9, 68, 0x5F); text(41, 9, 65, 0x5F); text(42, 9, 84, 0x5F); text(43, 9, 65, 0x5F)
    text(27, 11, 72, 0x5F); text(28, 11, 73, 0x5F); text(29, 11, 71, 0x5F); text(30, 11, 72, 0x5F)
    text(32, 11, 83, 0x5F); text(33, 11, 67, 0x5F); text(34, 11, 79, 0x5F); text(35, 11, 82, 0x5F); text(36, 11, 69, 0x5F)
    text(38, 11, 65, 0x5F); text(39, 11, 78, 0x5F); text(40, 11, 68, 0x5F)
    text(42, 11, 83, 0x5F); text(43, 11, 69, 0x5F); text(44, 11, 84, 0x5F); text(45, 11, 84, 0x5F)
    text(46, 11, 73, 0x5F); text(47, 11, 78, 0x5F); text(48, 11, 71, 0x5F); text(49, 11, 83, 0x5F)
    text(32, 13, 87, 0x5F); text(33, 13, 73, 0x5F); text(34, 13, 76, 0x5F); text(35, 13, 76, 0x5F)
    text(37, 13, 66, 0x5F); text(38, 13, 69, 0x5F)
    text(40, 13, 68, 0x5F); text(41, 13, 69, 0x5F); text(42, 13, 76, 0x5F); text(43, 13, 69, 0x5F)
    yes_colour: i32 = 0x2F if reset_choice == 0 else 0x5F
    no_colour: i32 = 0x2F if reset_choice == 1 else 0x5F
    text(30, 16, 89, yes_colour); text(31, 16, 69, yes_colour); text(32, 16, 83, yes_colour)
    text(47, 16, 78, no_colour); text(48, 16, 79, no_colour)
    if reset_choice == 0: text(28, 16, 16, 0x5E)
    else: text(45, 16, 16, 0x5E)

def shape(k: i32, r: i32) -> i32:
    # 4x4 bit masks, row-major. I,O,T,S,Z,J,L; rotations share this compact ABI.
    if k == 0: return 0x00F0 if r % 2 == 0 else 0x4444
    if k == 1: return 0x0660
    if k == 2:
        if r == 0: return 0x0720
        if r == 1: return 0x2620
        if r == 2: return 0x0270
        return 0x2320
    if k == 3: return 0x0360 if r % 2 == 0 else 0x4620
    if k == 4: return 0x0630 if r % 2 == 0 else 0x2640
    if k == 5:
        if r == 0: return 0x0710
        if r == 1: return 0x2260
        if r == 2: return 0x0470
        return 0x3220
    if r == 0: return 0x0740
    if r == 1: return 0x6220
    if r == 2: return 0x0170
    return 0x2230

def fits(nx: i32, ny: i32, nr: i32) -> bool:
    mask: i32 = shape(kind, nr)
    cell: i32 = 0
    while cell < 16:
        if (mask & (1 << cell)) != 0:
            bx: i32 = nx + cell % 4
            by: i32 = ny + cell // 4
            if bx < 0 or bx >= 10 or by < -4 or by >= 20:
                return False
            if board_get((by + 4) * 10 + bx) != 0:
                return False
        cell = cell + 1
    return True

def merge_piece() -> None:
    global merge_count
    merge_count = merge_count + 1
    mask: i32 = shape(kind, rotation)
    cell: i32 = 0
    while cell < 16:
        if (mask & (1 << cell)) != 0:
            bx: i32 = piece_x + cell % 4
            by: i32 = piece_y + cell // 4
            if by >= -4 and by < 20:
                board_set((by + 4) * 10 + bx, kind + 1)
        cell = cell + 1

def clear_lines() -> None:
    global score
    # Scan all 24 physical rows, including the four-row spawn buffer.
    y: i32 = 23
    while y >= 0:
        full: i32 = 1
        x: i32 = 0
        while x < 10:
            if board_get(y * 10 + x) == 0: full = 0
            x = x + 1
        if full == 1:
            row: i32 = y
            while row > 0:
                x = 0
                while x < 10:
                    board_set(row * 10 + x, board_get((row - 1) * 10 + x))
                    x = x + 1
                row = row - 1
            x = 0
            while x < 10:
                board_set(x, 0)
                x = x + 1
            score = score + 100
        else:
            y = y - 1

def spawn() -> None:
    global kind, rotation, piece_x, piece_y, next_kind, game_over, hold_used, grounded
    kind = next_kind
    next_kind = (next_kind + 3) % 7
    rotation = 0
    piece_x = 3
    piece_y = -1
    hold_used = 0
    grounded = 0
    if not fits(piece_x, piece_y, rotation): game_over = 1

def hold_piece() -> None:
    global kind, held_kind, rotation, piece_x, piece_y, next_kind, hold_used, game_over, grounded
    old_kind: i32 = kind
    if held_kind < 0:
        held_kind = old_kind
        kind = next_kind
        next_kind = (next_kind + 3) % 7
    else:
        kind = held_kind
        held_kind = old_kind
    rotation = 0
    piece_x = 3
    piece_y = -1
    hold_used = 1
    grounded = 0
    if not fits(piece_x, piece_y, rotation): game_over = 1

def put_number(value: i32, x: i32, y: i32) -> None:
    # fixed five-digit score display
    divisor: i32 = 10000
    cursor: i32 = x
    while divisor > 0:
        text(cursor, y, 48 + (value // divisor) % 10, 0x0F)
        cursor = cursor + 1
        divisor = divisor // 10

def draw_preview(preview_kind: i32, origin_x: i32, origin_y: i32) -> None:
    row: i32 = 0
    while row < 4:
        column: i32 = 0
        while column < 8:
            ui_put_cell(origin_x + column, origin_y + row, 32, 0x10)
            column = column + 1
        row = row + 1
    if preview_kind >= 0:
        preview_mask: i32 = shape(preview_kind, 0)
        preview_cell: i32 = 0
        preview_colour: i32 = 0x09 + (preview_kind + 1) % 6
        while preview_cell < 16:
            if (preview_mask & (1 << preview_cell)) != 0:
                px: i32 = origin_x + (preview_cell % 4) * 2
                py: i32 = origin_y + preview_cell // 4
                ui_put_cell(px, py, 219, preview_colour)
                ui_put_cell(px + 1, py, 219, preview_colour)
            preview_cell = preview_cell + 1

def debug_status() -> None:
    global debug_filled, debug_started, debug_game_over, debug_grounded, debug_piece_y, debug_merge_count, debug_banner_drawn
    filled: i32 = 0
    index: i32 = 0
    while index < 240:
        if board_get(index) != 0:
            filled = filled + 1
        index = index + 1
    if debug_banner_drawn == 0:
        text(1, 24, 68, 0x0F); text(2, 24, 66, 0x0F); text(3, 24, 71, 0x0F)
        text(5, 24, 70, 0x0B); text(6, 24, 58, 0x07)
        text(10, 24, 83, 0x0B); text(11, 24, 58, 0x07)
        text(15, 24, 79, 0x0B); text(16, 24, 58, 0x07)
        text(20, 24, 71, 0x0B); text(21, 24, 58, 0x07)
        text(25, 24, 89, 0x0B); text(26, 24, 58, 0x07)
        text(30, 24, 77, 0x0B); text(31, 24, 58, 0x07)
        debug_banner_drawn = 1
    if filled != debug_filled:
        put_hex8(filled, 7, 24)
        debug_filled = filled
    if started != debug_started:
        put_hex8(started, 12, 24)
        debug_started = started
    if game_over != debug_game_over:
        put_hex8(game_over, 17, 24)
        debug_game_over = game_over
    if grounded != debug_grounded:
        put_hex8(grounded, 22, 24)
        debug_grounded = grounded
    if piece_y != debug_piece_y:
        put_hex8(piece_y + 10, 27, 24)
        debug_piece_y = piece_y
    if merge_count != debug_merge_count:
        put_hex8(merge_count, 32, 24)
        debug_merge_count = merge_count

def debug_reset() -> None:
    global debug_filled, debug_started, debug_game_over, debug_grounded, debug_piece_y, debug_merge_count, debug_banner_drawn
    debug_filled = -1
    debug_started = -1
    debug_game_over = -1
    debug_grounded = -1
    debug_piece_y = -100
    debug_merge_count = -1
    debug_banner_drawn = 0

def draw() -> None:
    # Official playfield: exactly 10 columns x 20 visible rows. Each logical
    # cell occupies two VGA character columns so blocks look nearly square.
    y: i32 = 0
    while y < 20:
        x: i32 = 0
        while x < 10:
            value: i32 = board_get((y + 4) * 10 + x)
            colour: i32 = 0x10
            glyph: i32 = 32
            if value != 0:
                # value is kind + 1. Match the falling piece exactly.
                colour = 0x09 + value % 6
                glyph = 219
            ui_put_cell(5 + x * 2, 2 + y, glyph, colour)
            ui_put_cell(6 + x * 2, 2 + y, glyph, colour)
            x = x + 1
        y = y + 1

    # CP437 double-line border around the 10x20 field.
    y = 2
    while y < 22:
        ui_put_cell(4, y, 186, 0x1B)
        ui_put_cell(25, y, 186, 0x1B)
        y = y + 1
    x = 5
    while x < 25:
        ui_put_cell(x, 1, 205, 0x1B)
        ui_put_cell(x, 22, 205, 0x1B)
        x = x + 1
    ui_put_cell(4, 1, 201, 0x1B); ui_put_cell(25, 1, 187, 0x1B)
    ui_put_cell(4, 22, 200, 0x1B); ui_put_cell(25, 22, 188, 0x1B)

    mask: i32 = shape(kind, rotation)
    cell: i32 = 0
    active_colour: i32 = 0x09 + (kind + 1) % 6
    while cell < 16:
        if (mask & (1 << cell)) != 0:
            block_x: i32 = 5 + (piece_x + cell % 4) * 2
            block_y: i32 = 2 + piece_y + cell // 4
            if block_y >= 2:
                ui_put_cell(block_x, block_y, 219, active_colour)
                ui_put_cell(block_x + 1, block_y, 219, active_colour)
        cell = cell + 1

    text(31, 3, 83, 0x0F); text(32, 3, 67, 0x0F)
    text(33, 3, 79, 0x0F); text(34, 3, 82, 0x0F)
    text(35, 3, 69, 0x0F); text(36, 3, 58, 0x0F)
    put_number(score, 31, 5)
    text(31, 6, 72, 0x0E); text(32, 6, 73, 0x0E); text(33, 6, 71, 0x0E); text(34, 6, 72, 0x0E); text(35, 6, 58, 0x0E)
    put_number(high_score, 37, 6)
    # In-game controls and hold status.
    text(31, 8, 65, 0x0B); text(32, 8, 82, 0x0B); text(33, 8, 82, 0x0B)
    text(34, 8, 79, 0x0B); text(35, 8, 87, 0x0B); text(36, 8, 83, 0x0B)
    text(38, 8, 77, 0x07); text(39, 8, 79, 0x07); text(40, 8, 86, 0x07); text(41, 8, 69, 0x07)
    text(31, 10, 85, 0x0B); text(32, 10, 80, 0x0B)
    text(34, 10, 82, 0x07); text(35, 10, 79, 0x07); text(36, 10, 84, 0x07)
    text(37, 10, 65, 0x07); text(38, 10, 84, 0x07); text(39, 10, 69, 0x07)
    text(31, 12, 68, 0x0B); text(32, 12, 79, 0x0B); text(33, 12, 87, 0x0B); text(34, 12, 78, 0x0B)
    text(36, 12, 68, 0x07); text(37, 12, 82, 0x07); text(38, 12, 79, 0x07); text(39, 12, 80, 0x07)
    text(31, 14, 67, 0x0E); text(33, 14, 72, 0x07); text(34, 14, 79, 0x07)
    text(35, 14, 76, 0x07); text(36, 14, 68, 0x07)
    text(31, 16, 72, 0x0F); text(32, 16, 79, 0x0F); text(33, 16, 76, 0x0F)
    text(34, 16, 68, 0x0F); text(35, 16, 58, 0x0F)
    if held_kind < 0:
        text(37, 16, 45, 0x08)
    else:
        text(37, 16, 49 + held_kind, 0x0E)
    text(31, 19, 69, 0x0C); text(32, 19, 83, 0x0C); text(33, 19, 67, 0x0C)
    text(35, 19, 80, 0x07); text(36, 19, 65, 0x07); text(37, 19, 85, 0x07)
    text(38, 19, 83, 0x07); text(39, 19, 69, 0x07)
    draw_preview(held_kind, 44, 15)
    if game_over == 1:
        text(31, 8, 71, 0x0C); text(32, 8, 65, 0x0C)
        text(33, 8, 77, 0x0C); text(34, 8, 69, 0x0C)

def boot_logo_row(letter: i32, row: i32) -> i32:
    # Five-bit rows for a tetromino-style T E T R I S logo.
    if letter == 0 or letter == 2:
        return 31 if row == 0 else 4
    if letter == 1:
        if row == 0 or row == 4: return 31
        if row == 2: return 30
        return 16
    if letter == 3:
        if row == 0 or row == 2: return 30
        if row == 1: return 17
        if row == 3: return 20
        return 18
    if letter == 4:
        return 31 if row == 0 or row == 4 else 4
    if row == 0: return 15
    if row == 1: return 16
    if row == 2: return 14
    if row == 3: return 1
    return 30


def boot_wait(periods: i32) -> None:
    pit_reset_elapsed()
    while pit_poll_elapsed(periods) == 0:
        pass


def boot_screen() -> None:
    clear_screen(0x10)
    letter: i32 = 0
    while letter < 6:
        row: i32 = 0
        logo_colour: i32 = 0x09 + letter % 6
        while row < 5:
            bits: i32 = boot_logo_row(letter, row)
            column: i32 = 0
            while column < 5:
                if (bits & (1 << (4 - column))) != 0:
                    screen_x: i32 = 4 + letter * 12 + column * 2
                    ui_put_cell(screen_x, 2 + row, 219, logo_colour)
                    ui_put_cell(screen_x + 1, 2 + row, 219, logo_colour)
                column = column + 1
            row = row + 1
        letter = letter + 1
    # TETRIS OS / PYTHON KERNEL
    text(34, 9, 84, 0x0E); text(35, 9, 69, 0x0E); text(36, 9, 84, 0x0E)
    text(37, 9, 82, 0x0E); text(38, 9, 73, 0x0E); text(39, 9, 83, 0x0E)
    text(41, 9, 79, 0x0B); text(42, 9, 83, 0x0B)
    text(33, 11, 80, 0x07); text(34, 11, 89, 0x07); text(35, 11, 84, 0x07)
    text(36, 11, 72, 0x07); text(37, 11, 79, 0x07); text(38, 11, 78, 0x07)
    text(40, 11, 75, 0x07); text(41, 11, 69, 0x07); text(42, 11, 82, 0x07)
    text(43, 11, 78, 0x07); text(44, 11, 69, 0x07); text(45, 11, 76, 0x07)
    # Real boot checks.
    text(24, 14, 80, 0x07); text(25, 14, 73, 0x07); text(26, 14, 84, 0x07)
    text(28, 14, 84, 0x07); text(29, 14, 73, 0x07); text(30, 14, 77, 0x07); text(31, 14, 69, 0x07); text(32, 14, 82, 0x07)
    text(51, 14, 79, 0x0A); text(52, 14, 75, 0x0A)
    fs_mount()
    text(24, 16, 73, 0x07); text(25, 16, 68, 0x07); text(26, 16, 69, 0x07)
    text(28, 16, 84, 0x07); text(29, 16, 73, 0x07); text(30, 16, 78, 0x07); text(31, 16, 89, 0x07)
    text(32, 16, 70, 0x07); text(33, 16, 83, 0x07)
    if fs_ready == 1:
        text(51, 16, 79, 0x0A); text(52, 16, 75, 0x0A)
    else:
        text(48, 16, 79, 0x0E); text(49, 16, 70, 0x0E); text(50, 16, 70, 0x0E)
        text(51, 16, 76, 0x0E); text(52, 16, 73, 0x0E); text(53, 16, 78, 0x0E); text(54, 16, 69, 0x0E)
    text(24, 18, 72, 0x07); text(25, 18, 73, 0x07); text(26, 18, 71, 0x07); text(27, 18, 72, 0x07)
    text(29, 18, 83, 0x07); text(30, 18, 67, 0x07); text(31, 18, 79, 0x07); text(32, 18, 82, 0x07); text(33, 18, 69, 0x07)
    put_number(high_score, 48, 18)
    # PIT-paced loading bar, about one second total.
    progress: i32 = 0
    while progress < 50:
        ui_put_cell(15 + progress, 21, 219, 0x0B)
        boot_wait(2)
        progress = progress + 1
    boot_wait(20)

def reset_game() -> None:
    global kind, rotation, piece_x, piece_y, next_kind, score, game_over, held_kind, hold_used, grounded, game_initialized, merge_count, game_over_drawn
    index: i32 = 0
    while index < 240:
        board_set(index, 0)
        index = index + 1
    kind = 0
    rotation = 0
    piece_x = 3
    piece_y = -1
    next_kind = 1
    score = 0
    game_over = 0
    held_kind = -1
    hold_used = 0
    grounded = 0
    merge_count = 0
    game_over_drawn = 0
    spawn()
    game_initialized = 1


def draw_game_over() -> None:
    # PIT-paced curtains sweep inward from both sides in about 400 ms.
    inset: i32 = 0
    while inset < 40:
        y: i32 = 0
        while y < 25:
            ui_put_cell(inset, y, 32, 0x00)
            ui_put_cell(79 - inset, y, 32, 0x00)
            y = y + 1
        pit_reset_elapsed()
        while pit_poll_elapsed(1) == 0:
            pass
        inset = inset + 1
    # GAME OVER
    ui_put_cell(35, 10, 71, 0x0C); ui_put_cell(36, 10, 65, 0x0C)
    ui_put_cell(37, 10, 77, 0x0C); ui_put_cell(38, 10, 69, 0x0C)
    ui_put_cell(40, 10, 79, 0x0C); ui_put_cell(41, 10, 86, 0x0C)
    ui_put_cell(42, 10, 69, 0x0C); ui_put_cell(43, 10, 82, 0x0C)
    # ENTER: HOME
    ui_put_cell(34, 13, 69, 0x0F); ui_put_cell(35, 13, 78, 0x0F)
    ui_put_cell(36, 13, 84, 0x0F); ui_put_cell(37, 13, 69, 0x0F)
    ui_put_cell(38, 13, 82, 0x0F); ui_put_cell(39, 13, 58, 0x0F)
    ui_put_cell(41, 13, 72, 0x0B); ui_put_cell(42, 13, 79, 0x0B)
    ui_put_cell(43, 13, 77, 0x0B); ui_put_cell(44, 13, 69, 0x0B)

def kernel_main() -> None:
    global piece_x, piece_y, rotation, ticks, key_cooldown, started, last_key, menu_drawn, grounded, game_initialized, game_over_drawn, debug_visible, menu_page, menu_selection, settings_selection, reset_choice, color_mode, gravity_periods
    vga_set_mode13()
    cell: i32 = 0
    while cell < 240:
        board_set(cell, 0)
        cell = cell + 1
    pit_init()
    boot_screen()
    vga_set_palette(color_mode)
    redraw: i32 = 0
    while True:
        redraw = 0
        key: i32 = keyboard_scancode()
        if key != 0:
            last_key = key
        if key == 0x2A or key == 0x36:
            debug_visible = 0 if debug_visible == 1 else 1
            debug_reset()
            if started == 0:
                menu_drawn = 0
            elif debug_visible == 0:
                debug_x: i32 = 0
                debug_background: i32 = 0x00 if game_over == 1 else 0x10
                while debug_x < 80:
                    ui_put_cell(debug_x, 24, 32, debug_background)
                    debug_x = debug_x + 1

        if started == 0:
            if menu_drawn == 0:
                if menu_page == 0:
                    draw_menu()
                elif menu_page == 1:
                    draw_settings()
                else:
                    draw_reset_dialog()
                menu_drawn = 1
                debug_reset()
            elif debug_visible == 1 and menu_page == 0 and key != 0:
                put_hex8(last_key, 48, 19)

            if menu_page == 0:
                if key == 0x48:
                    menu_selection = (menu_selection + 2) % 3
                    menu_drawn = 0
                elif key == 0x50:
                    menu_selection = (menu_selection + 1) % 3
                    menu_drawn = 0
                elif key == 0x1C:
                    if menu_selection == 0:
                        started = 1
                        clear_screen(0x10)
                        if game_initialized == 0:
                            reset_game()
                        arm_move_cooldown(15)
                        debug_reset()
                        draw()
                    elif menu_selection == 1:
                        menu_page = 1
                        settings_selection = 0
                        menu_drawn = 0
                    else:
                        menu_page = 2
                        reset_choice = 1
                        menu_drawn = 0
            elif menu_page == 1:
                if key == 0x48:
                    settings_selection = (settings_selection + 2) % 3
                    menu_drawn = 0
                elif key == 0x50:
                    settings_selection = (settings_selection + 1) % 3
                    menu_drawn = 0
                elif key == 0x4B:
                    if settings_selection == 0:
                        color_mode = (color_mode + 2) % 3
                        vga_set_palette(color_mode)
                        menu_drawn = 0
                    elif settings_selection == 1 and gravity_periods > 10:
                        gravity_periods = gravity_periods - 10
                        menu_drawn = 0
                elif key == 0x4D:
                    if settings_selection == 0:
                        color_mode = (color_mode + 1) % 3
                        vga_set_palette(color_mode)
                        menu_drawn = 0
                    elif settings_selection == 1 and gravity_periods < 100:
                        gravity_periods = gravity_periods + 10
                        menu_drawn = 0
                elif key == 0x1C and settings_selection == 2:
                    fs_save_settings()
                    menu_page = 0
                    menu_drawn = 0
                elif key == 0x01:
                    fs_save_settings()
                    menu_page = 0
                    menu_drawn = 0
            else:
                if key == 0x4B or key == 0x4D:
                    reset_choice = 1 - reset_choice
                    menu_drawn = 0
                elif key == 0x1C:
                    if reset_choice == 0:
                        fs_reset_data()
                        vga_set_palette(0)
                    menu_page = 0
                    menu_selection = 0
                    menu_drawn = 0
                elif key == 0x01:
                    menu_page = 0
                    menu_drawn = 0

        elif game_over == 0:
            if key == 0x01:
                started = 0
                menu_page = 0
                menu_drawn = 0
                arm_move_cooldown(15)
            if move_ready() and key == 0x4B and fits(piece_x - 1, piece_y, rotation):
                piece_x = piece_x - 1
                arm_move_cooldown(10)
                redraw = 1
            if move_ready() and key == 0x4D and fits(piece_x + 1, piece_y, rotation):
                piece_x = piece_x + 1
                arm_move_cooldown(10)
                redraw = 1
            if move_ready() and key == 0x50 and fits(piece_x, piece_y + 1, rotation):
                piece_y = piece_y + 1
                arm_move_cooldown(5)
                redraw = 1
                if not fits(piece_x, piece_y + 1, rotation):
                    grounded = 1
                    pit_reset_elapsed()
            if move_ready() and key == 0x48 and fits(piece_x, piece_y, (rotation + 1) % 4):
                rotation = (rotation + 1) % 4
                arm_move_cooldown(15)
                redraw = 1
            if move_ready() and key == 0x2E:
                hold_piece()
                arm_move_cooldown(15)
                redraw = 1
            timer_ready: i32 = pit_poll_elapsed(20 if grounded == 1 else gravity_periods)
            if timer_ready != 0:
                if grounded == 1 and not fits(piece_x, piece_y + 1, rotation):
                    merge_piece()
                    clear_lines()
                    spawn()
                    redraw = 1
                elif fits(piece_x, piece_y + 1, rotation):
                    grounded = 0
                    piece_y = piece_y + 1
                    redraw = 1
                    if not fits(piece_x, piece_y + 1, rotation):
                        grounded = 1
                        pit_reset_elapsed()
                else:
                    grounded = 1
                    pit_reset_elapsed()
            if redraw == 1:
                draw()
        else:
            if game_over_drawn == 0:
                fs_save_high_score(score)
                draw_game_over()
                game_over_drawn = 1
            if key == 0x1C:
                started = 0
                menu_page = 0
                menu_drawn = 0
                game_initialized = 0
                game_over_drawn = 0
                arm_move_cooldown(15)
                debug_reset()
        if debug_visible == 1 and started == 1:
            debug_status()


kernel_main()
