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
    global merge_count, total_pieces
    merge_count = merge_count + 1
    total_pieces = total_pieces + 1
    unlock_achievement(0)
    if total_pieces >= 100: unlock_achievement(3)
    mask: i32 = shape(kind, rotation)
    cell: i32 = 0
    while cell < 16:
        if (mask & (1 << cell)) != 0:
            bx: i32 = piece_x + cell % 4
            by: i32 = piece_y + cell // 4
            if by >= -4 and by < 20:
                board_set((by + 4) * 10 + bx, kind + 1)
        cell = cell + 1

def clear_lines() -> i32:
    global score
    cleared: i32 = 0
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
            cleared = cleared + 1
        else:
            y = y - 1
    return cleared

def update_combo(cleared: i32) -> None:
    global current_combo, score, total_lines, session_lines
    if cleared > 0:
        total_lines = total_lines + cleared
        session_lines = session_lines + cleared
        unlock_achievement(1)
        if cleared >= 4: unlock_achievement(2)
        if total_lines >= 100: unlock_achievement(5)
        current_combo = current_combo + 1
        if current_combo > 1:
            score = score + (current_combo - 1) * 50
        fs_save_max_combo(current_combo)
        if current_combo >= 3: unlock_achievement(7)
        if current_combo >= 8: unlock_achievement(8)
        if score >= 10000: unlock_achievement(4)
    else:
        current_combo = 0
def seed_rng() -> None:
    global rng_state
    timer_sample: i32 = pit_latch_current()
    rng_state = (timer_sample ^ (system_periods * 25173) ^ (last_key * 257) ^ 0xA361) & 0xFFFF
    if rng_state == 0:
        rng_state = 1
def random_bounded(limit: i32) -> i32:
    global rng_state
    rng_state = (rng_state * 25173 + 13849) % 65536
    return rng_state % limit

def refill_bag() -> None:
    global bag_index, last_bag_kind
    index: i32 = 0
    while index < 7:
        bag_set(index, index)
        index = index + 1
    index = 6
    while index > 0:
        swap_index: i32 = random_bounded(index + 1)
        value: i32 = bag_get(index)
        bag_set(index, bag_get(swap_index))
        bag_set(swap_index, value)
        index = index - 1
    # A normal 7-bag may repeat across its boundary. Keep all seven pieces
    # while swapping the new first piece when it equals the previous last one.
    if last_bag_kind >= 0 and bag_get(0) == last_bag_kind:
        swap_index = 1 + random_bounded(6)
        value = bag_get(0)
        bag_set(0, bag_get(swap_index))
        bag_set(swap_index, value)
    bag_index = 0

def take_bag() -> i32:
    global bag_index, last_bag_kind
    if bag_index >= 7:
        refill_bag()
    result: i32 = bag_get(bag_index)
    bag_index = bag_index + 1
    last_bag_kind = result
    return result

def spawn() -> None:
    global kind, rotation, piece_x, piece_y, next_kind, game_over, hold_used, grounded
    kind = next_kind
    next_kind = take_bag()
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
        next_kind = take_bag()
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
        preview_colour: i32 = 0x0A + preview_kind % 6
        while preview_cell < 16:
            if (preview_mask & (1 << preview_cell)) != 0:
                px: i32 = origin_x + (preview_cell % 4) * 2
                py: i32 = origin_y + preview_cell // 4
                ui_put_cell(px, py, 219, preview_colour)
                ui_put_cell(px + 1, py, 219, preview_colour)
            preview_cell = preview_cell + 1

def debug_status() -> None:
    global debug_filled, debug_started, debug_game_over, debug_grounded, debug_piece_y, debug_merge_count, debug_banner_drawn, fps_value
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
        text(36, 24, 70, 0x0A); text(37, 24, 80, 0x0A); text(38, 24, 83, 0x0A); text(39, 24, 58, 0x07)
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
    put_hex8(fps_value, 40, 24)

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
    global fps_frames
    fps_frames = fps_frames + 1
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
                colour = 0x0A + (value - 1) % 6
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
    active_colour: i32 = 0x0A + kind % 6
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
    text(55, 9, 67, 0x0B); text(56, 9, 79, 0x0B); text(57, 9, 77, 0x0B)
    text(58, 9, 66, 0x0B); text(59, 9, 79, 0x0B); text(60, 9, 58, 0x0B)
    put_number(current_combo, 55, 10)
    text(55, 12, 66, 0x0E); text(56, 12, 69, 0x0E); text(57, 12, 83, 0x0E); text(58, 12, 84, 0x0E); text(59, 12, 58, 0x0E)
    put_number(max_combo, 55, 13)
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
    # The upcoming tetromino is always visible in the free upper-right panel.
    text(44, 2, 78, 0x0F); text(45, 2, 69, 0x0F)
    text(46, 2, 88, 0x0F); text(47, 2, 84, 0x0F); text(48, 2, 58, 0x0F)
    draw_preview(next_kind, 44, 4)
    if (achievements & (1 << 12)) != 0 and clock_enabled == 1:
        elapsed_rtc: i32 = rtc_seconds_of_day() - game_start_rtc
        if elapsed_rtc < 0: elapsed_rtc = elapsed_rtc + 86400
        minutes: i32 = elapsed_rtc // 60
        seconds: i32 = elapsed_rtc % 60
        text(55, 16, 67, 0x0E); text(56, 16, 76, 0x0E); text(57, 16, 79, 0x0E); text(58, 16, 67, 0x0E); text(59, 16, 75, 0x0E)
        text(61, 16, 48 + (minutes // 10) % 10, 0x0F); text(62, 16, 48 + minutes % 10, 0x0F); text(63, 16, 58, 0x0F)
        text(64, 16, 48 + seconds // 10, 0x0F); text(65, 16, 48 + seconds % 10, 0x0F)
    draw_achievement_popup()
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

def finish_session() -> None:
    if session_silent == 1: unlock_achievement(10)
    if session_palette == 1 and session_lines >= 10: unlock_achievement(11)
    if session_palette == 2 and score >= 1000: unlock_achievement(12)
    fs_save_statistics()
def reset_game() -> None:
    global kind, rotation, piece_x, piece_y, next_kind, score, game_over, held_kind, hold_used, grounded, game_initialized, merge_count, game_over_drawn, bag_index, last_bag_kind, rng_state, current_combo, session_lines, session_silent, session_palette, game_start_rtc
    index: i32 = 0
    while index < 240:
        board_set(index, 0)
        index = index + 1
    kind = 0
    rotation = 0
    piece_x = 3
    piece_y = -1
    bag_index = 7
    last_bag_kind = -1
    seed_rng()
    next_kind = take_bag()
    score = 0
    game_over = 0
    held_kind = -1
    hold_used = 0
    grounded = 0
    merge_count = 0
    current_combo = 0
    session_lines = 0
    session_silent = 1 if bgm_volume == 0 and se_volume == 0 else 0
    session_palette = color_mode
    game_start_rtc = rtc_seconds_of_day()
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
            sound_update()
        sound_update()
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
