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
settings_page: i32 = 0
reset_choice: i32 = 1
held_kind: i32 = -1
hold_used: i32 = 0
grounded: i32 = 0
game_initialized: i32 = 0
game_over_drawn: i32 = 0
merge_count: i32 = 0
current_combo: i32 = 0
debug_filled: i32 = -1
debug_started: i32 = -1
debug_game_over: i32 = -1
debug_grounded: i32 = -1
debug_piece_y: i32 = -100
debug_merge_count: i32 = -1
debug_banner_drawn: i32 = 0
debug_visible: i32 = 0
fps_frames: i32 = 0
fps_value: i32 = 0
fps_deadline: i32 = 100

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


def draw_menu_label(item: i32, y: i32) -> None:
    colour: i32 = 0x2F if menu_selection == item else 0x1F
    if item == 0:
        text(37, y, 80, colour); text(38, y, 76, colour); text(39, y, 65, colour); text(40, y, 89, colour)
    elif item == 1:
        text(35, y, 83, colour); text(36, y, 69, colour); text(37, y, 84, colour); text(38, y, 84, colour); text(39, y, 73, colour); text(40, y, 78, colour); text(41, y, 71, colour); text(42, y, 83, colour)
    elif item == 2:
        text(34, y, 82, colour); text(35, y, 69, colour); text(36, y, 83, colour); text(37, y, 69, colour); text(38, y, 84, colour)
        text(40, y, 68, colour); text(41, y, 65, colour); text(42, y, 84, colour); text(43, y, 65, colour)
    else:
        text(34, y, 83, colour); text(35, y, 84, colour); text(36, y, 65, colour); text(37, y, 84, colour); text(38, y, 73, colour)
        text(39, y, 83, colour); text(40, y, 84, colour); text(41, y, 73, colour); text(42, y, 67, colour); text(43, y, 83, colour)

def draw_menu() -> None:
    draw_menu_shell(0)
    first_item: i32 = 1 if menu_selection == 3 else 0
    item: i32 = 0
    while item < 3:
        visible_item: i32 = first_item + item
        button_y: i32 = 6 + item * 4
        draw_menu_button(visible_item, button_y)
        draw_menu_label(visible_item, button_y + 1)
        item = item + 1
    text(32, 19, 85, 0x07); text(33, 19, 80, 0x07)
    text(35, 19, 68, 0x07); text(36, 19, 79, 0x07); text(37, 19, 87, 0x07); text(38, 19, 78, 0x07)
    text(40, 19, 69, 0x07); text(41, 19, 78, 0x07); text(42, 19, 84, 0x07); text(43, 19, 69, 0x07); text(44, 19, 82, 0x07)
    if debug_visible == 1: put_hex8(last_key, 48, 19)
def draw_setting_value(value: i32, x: i32, y: i32) -> None:
    text(x, y, 48 + value // 10, 0x0F)
    text(x + 1, y, 48 + value % 10, 0x0F)

def draw_settings() -> None:
    draw_menu_shell(1)
    text(34, 4, 80, 0x0E); text(35, 4, 65, 0x0E); text(36, 4, 71, 0x0E); text(37, 4, 69, 0x0E)
    text(39, 4, 49 + settings_page, 0x0F); text(40, 4, 47, 0x07); text(41, 4, 50, 0x0F)
    cursor_y: i32 = 6 + settings_selection * 3 if settings_selection < 3 else 17
    text(20, cursor_y, 16, 0x0E)
    if settings_page == 0:
        # COLOR
        text(24, 6, 67, 0x0B); text(25, 6, 79, 0x0B); text(26, 6, 76, 0x0B); text(27, 6, 79, 0x0B); text(28, 6, 82, 0x0B)
        if color_mode == 0:
            text(42, 6, 78, 0x0F); text(43, 6, 79, 0x0F); text(44, 6, 82, 0x0F); text(45, 6, 77, 0x0F); text(46, 6, 65, 0x0F); text(47, 6, 76, 0x0F)
        elif color_mode == 1:
            text(39, 6, 71, 0x0F); text(40, 6, 82, 0x0F); text(41, 6, 65, 0x0F); text(42, 6, 89, 0x0F); text(43, 6, 83, 0x0F); text(44, 6, 67, 0x0F); text(45, 6, 65, 0x0F); text(46, 6, 76, 0x0F); text(47, 6, 69, 0x0F)
        else:
            text(40, 6, 73, 0x0F); text(41, 6, 78, 0x0F); text(42, 6, 86, 0x0F); text(43, 6, 69, 0x0F); text(44, 6, 82, 0x0F); text(45, 6, 84, 0x0F)
        # GRAVITY
        text(24, 9, 71, 0x0B); text(25, 9, 82, 0x0B); text(26, 9, 65, 0x0B); text(27, 9, 86, 0x0B); text(28, 9, 73, 0x0B); text(29, 9, 84, 0x0B); text(30, 9, 89, 0x0B)
        put_number(gravity_periods * 10, 41, 9); text(47, 9, 77, 0x07); text(48, 9, 83, 0x07)
        # CONTROL
        text(24, 12, 67, 0x0B); text(25, 12, 79, 0x0B); text(26, 12, 78, 0x0B); text(27, 12, 84, 0x0B); text(28, 12, 82, 0x0B); text(29, 12, 79, 0x0B); text(30, 12, 76, 0x0B)
        if control_mode == 0:
            text(42, 12, 65, 0x0F); text(43, 12, 82, 0x0F); text(44, 12, 82, 0x0F); text(45, 12, 79, 0x0F); text(46, 12, 87, 0x0F); text(47, 12, 83, 0x0F)
        else:
            text(43, 12, 87, 0x0F); text(44, 12, 65, 0x0F); text(45, 12, 83, 0x0F); text(46, 12, 68, 0x0F)
        text(34, 17, 78, 0x0A); text(35, 17, 69, 0x0A); text(36, 17, 88, 0x0A); text(37, 17, 84, 0x0A); text(39, 17, 80, 0x0A); text(40, 17, 65, 0x0A); text(41, 17, 71, 0x0A); text(42, 17, 69, 0x0A)
    else:
        # BGM / SE volume
        text(24, 6, 66, 0x0B); text(25, 6, 71, 0x0B); text(26, 6, 77, 0x0B); text(28, 6, 86, 0x0B); text(29, 6, 79, 0x0B); text(30, 6, 76, 0x0B)
        draw_setting_value(bgm_volume, 45, 6)
        text(24, 9, 83, 0x0B); text(25, 9, 69, 0x0B); text(27, 9, 86, 0x0B); text(28, 9, 79, 0x0B); text(29, 9, 76, 0x0B)
        draw_setting_value(se_volume, 45, 9)
        # DEBUG
        text(24, 12, 68, 0x0B); text(25, 12, 69, 0x0B); text(26, 12, 66, 0x0B); text(27, 12, 85, 0x0B); text(28, 12, 71, 0x0B)
        if debug_enabled == 1:
            text(44, 12, 79, 0x0F); text(45, 12, 78, 0x0F)
        else:
            text(43, 12, 79, 0x08); text(44, 12, 70, 0x08); text(45, 12, 70, 0x08)
        text(34, 17, 83, 0x0A); text(35, 17, 65, 0x0A); text(36, 17, 86, 0x0A); text(37, 17, 69, 0x0A); text(39, 17, 66, 0x0A); text(40, 17, 65, 0x0A); text(41, 17, 67, 0x0A); text(42, 17, 75, 0x0A)
    text(25, 21, 85, 0x07); text(26, 21, 80, 0x07); text(28, 21, 68, 0x07); text(29, 21, 79, 0x07); text(30, 21, 87, 0x07)
    text(33, 21, 76, 0x07); text(34, 21, 69, 0x07); text(35, 21, 70, 0x07); text(36, 21, 84, 0x07); text(38, 21, 82, 0x07); text(39, 21, 73, 0x07); text(40, 21, 71, 0x07); text(41, 21, 72, 0x07); text(42, 21, 84, 0x07)
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

def put_number_coloured(value: i32, x: i32, y: i32, colour: i32) -> None:
    divisor: i32 = 10000
    cursor: i32 = x
    while divisor > 0:
        ui_put_cell(cursor, y, 48 + (value // divisor) % 10, colour)
        cursor = cursor + 1
        divisor = divisor // 10
def draw_statistics() -> None:
    draw_menu()
    y: i32 = 6
    while y < 20:
        x: i32 = 18
        while x < 62:
            ui_put_cell(x, y, 32, 0x30)
            x = x + 1
        y = y + 1
    x = 18
    while x < 62:
        ui_put_cell(x, 6, 205, 0x3F); ui_put_cell(x, 19, 205, 0x3F)
        x = x + 1
    y = 7
    while y < 19:
        ui_put_cell(18, y, 186, 0x3F); ui_put_cell(61, y, 186, 0x3F)
        y = y + 1
    ui_put_cell(18, 6, 201, 0x3F); ui_put_cell(61, 6, 187, 0x3F)
    ui_put_cell(18, 19, 200, 0x3F); ui_put_cell(61, 19, 188, 0x3F)
    # STATISTICS
    text(34, 8, 83, 0x3F); text(35, 8, 84, 0x3F); text(36, 8, 65, 0x3F); text(37, 8, 84, 0x3F); text(38, 8, 73, 0x3F)
    text(39, 8, 83, 0x3F); text(40, 8, 84, 0x3F); text(41, 8, 73, 0x3F); text(42, 8, 67, 0x3F); text(43, 8, 83, 0x3F)
    # PLAY TIME / LINES / PIECES
    text(23, 11, 80, 0x3B); text(24, 11, 76, 0x3B); text(25, 11, 65, 0x3B); text(26, 11, 89, 0x3B); text(28, 11, 84, 0x3B); text(29, 11, 73, 0x3B); text(30, 11, 77, 0x3B); text(31, 11, 69, 0x3B)
    put_number_coloured(total_play_periods // 100, 48, 11, 0x3F); text(54, 11, 83, 0x37)
    text(23, 13, 76, 0x3B); text(24, 13, 73, 0x3B); text(25, 13, 78, 0x3B); text(26, 13, 69, 0x3B); text(27, 13, 83, 0x3B)
    put_number_coloured(total_lines, 48, 13, 0x3F)
    text(23, 15, 80, 0x3B); text(24, 15, 73, 0x3B); text(25, 15, 69, 0x3B); text(26, 15, 67, 0x3B); text(27, 15, 69, 0x3B); text(28, 15, 83, 0x3B)
    put_number_coloured(total_pieces, 48, 15, 0x3F)
    text(31, 18, 69, 0x3F); text(32, 18, 78, 0x3F); text(33, 18, 84, 0x3F); text(34, 18, 69, 0x3F); text(35, 18, 82, 0x3F)
    text(37, 18, 79, 0x3F); text(38, 18, 82, 0x3F); text(40, 18, 69, 0x3F); text(41, 18, 83, 0x3F); text(42, 18, 67, 0x3F)
