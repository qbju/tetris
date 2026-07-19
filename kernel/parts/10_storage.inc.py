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
    fs_put_u32(80, 9); fs_put_u32(84, 80)
    if not ata_write_sector(1):
        return False
    fs_buffer_clear()
    if not ata_write_sector(8):
        return False
    fs_buffer_clear()
    if not ata_write_sector(9):
        return False
    fs_buffer_clear()
    if not ata_write_sector(10):
        return False
    fs_buffer_clear()
    if not ata_write_sector(12):
        return False
    fs_buffer_clear()
    return ata_write_sector(13)


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
    fs_put_u32(80, 9); fs_put_u32(84, 80)
    ata_write_sector(1)


def settings_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 83 or fs_buffer_get(offset + 1) != 84 or fs_buffer_get(offset + 2) != 2:
        return False
    generation: i32 = fs_get_u32(offset + 4)
    saved_colour: i32 = fs_get_u32(offset + 8)
    saved_gravity: i32 = fs_get_u32(offset + 12)
    saved_control: i32 = fs_get_u32(offset + 16)
    saved_bgm: i32 = fs_get_u32(offset + 20)
    saved_se: i32 = fs_get_u32(offset + 24)
    saved_debug: i32 = fs_get_u32(offset + 28)
    saved_clock: i32 = fs_get_u32(offset + 36)
    checksum: i32 = generation ^ saved_colour ^ saved_gravity ^ saved_control ^ saved_bgm ^ saved_se ^ saved_debug ^ 0x53545447
    if saved_clock >= 256: checksum = checksum ^ saved_clock
    return fs_get_u32(offset + 32) == checksum and (saved_clock == 0 or saved_clock == 256 or saved_clock == 257) and saved_colour >= 0 and saved_colour <= 4 and saved_gravity >= 10 and saved_gravity <= 100 and saved_control >= 0 and saved_control <= 1 and saved_bgm >= 0 and saved_bgm <= 10 and saved_se >= 0 and saved_se <= 10 and saved_debug >= 0 and saved_debug <= 1

def fs_load_settings() -> None:
    global color_mode, gravity_periods, control_mode, bgm_volume, se_volume, debug_enabled, clock_enabled, settings_generation, settings_slot
    color_mode = 0
    gravity_periods = 50
    control_mode = 0
    bgm_volume = 6
    se_volume = 5
    debug_enabled = 1
    clock_enabled = 1
    settings_generation = 0
    settings_slot = 0
    if not ata_read_sector(9):
        return
    valid_a: bool = settings_record_valid(0)
    valid_b: bool = settings_record_valid(40)
    generation_a: i32 = fs_get_u32(4) if valid_a else -1
    generation_b: i32 = fs_get_u32(44) if valid_b else -1
    offset: i32 = 0
    if valid_b and generation_b > generation_a:
        settings_slot = 1
        settings_generation = generation_b
        offset = 40
    elif valid_a:
        settings_generation = generation_a
    else:
        return
    color_mode = fs_get_u32(offset + 8)
    gravity_periods = fs_get_u32(offset + 12)
    control_mode = fs_get_u32(offset + 16)
    bgm_volume = fs_get_u32(offset + 20)
    se_volume = fs_get_u32(offset + 24)
    debug_enabled = fs_get_u32(offset + 28)
    saved_clock: i32 = fs_get_u32(offset + 36)
    clock_enabled = saved_clock - 256 if saved_clock >= 256 else 1

def fs_save_settings() -> None:
    global settings_generation, settings_slot
    if fs_ready == 0 or not ata_read_sector(9):
        return
    new_slot: i32 = 0 if settings_slot == 1 else 1
    offset: i32 = new_slot * 40
    generation: i32 = settings_generation + 1
    saved_clock: i32 = 256 + clock_enabled
    checksum: i32 = generation ^ color_mode ^ gravity_periods ^ control_mode ^ bgm_volume ^ se_volume ^ debug_enabled ^ saved_clock ^ 0x53545447
    fs_buffer_set(offset, 83); fs_buffer_set(offset + 1, 84)
    fs_buffer_set(offset + 2, 2); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation)
    fs_put_u32(offset + 8, color_mode)
    fs_put_u32(offset + 12, gravity_periods)
    fs_put_u32(offset + 16, control_mode)
    fs_put_u32(offset + 20, bgm_volume)
    fs_put_u32(offset + 24, se_volume)
    fs_put_u32(offset + 28, debug_enabled)
    fs_put_u32(offset + 32, checksum)
    fs_put_u32(offset + 36, saved_clock)
    if ata_write_sector(9):
        settings_generation = generation
        settings_slot = new_slot
def fs_reset_data() -> None:
    global high_score, high_generation, high_slot, color_mode, gravity_periods, settings_generation, settings_slot, control_mode, bgm_volume, se_volume, debug_enabled, clock_enabled, max_combo, combo_generation, combo_slot, total_play_periods, total_lines, total_pieces, stats_generation, stats_slot, achievements, achievement_generation, achievement_slot
    high_score = 0
    high_generation = 0
    high_slot = 0
    color_mode = 0
    gravity_periods = 50
    control_mode = 0
    bgm_volume = 6
    se_volume = 5
    debug_enabled = 1
    clock_enabled = 1
    settings_generation = 0
    settings_slot = 0
    max_combo = 0
    combo_generation = 0
    combo_slot = 0
    total_play_periods = 0
    total_lines = 0
    total_pieces = 0
    stats_generation = 0
    stats_slot = 0
    achievements = 0
    achievement_generation = 0
    achievement_slot = 0
    if fs_ready == 0:
        return
    fs_buffer_clear()
    ata_write_sector(8)
    fs_buffer_clear()
    ata_write_sector(9)
    fs_buffer_clear()
    ata_write_sector(10)
    fs_buffer_clear()
    ata_write_sector(12)
    fs_buffer_clear()
    ata_write_sector(13)

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
    fs_load_max_combo()
    fs_load_statistics()
    fs_load_achievements()
    if impossible_enabled == 1: unlock_achievement(13)


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

def achievement_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 65 or fs_buffer_get(offset + 1) != 67: return False
    generation: i32 = fs_get_u32(offset + 4)
    mask: i32 = fs_get_u32(offset + 8)
    return fs_get_u32(offset + 12) == (generation ^ mask ^ 0x41434856)

def fs_load_achievements() -> None:
    global achievements, achievement_generation, achievement_slot
    achievements = 0; achievement_generation = 0; achievement_slot = 0
    if not ata_read_sector(13): return
    valid_a: bool = achievement_record_valid(0)
    valid_b: bool = achievement_record_valid(16)
    ga: i32 = fs_get_u32(4) if valid_a else -1
    gb: i32 = fs_get_u32(20) if valid_b else -1
    if valid_b and gb > ga:
        achievement_slot = 1; achievement_generation = gb; achievements = fs_get_u32(24)
    elif valid_a:
        achievement_generation = ga; achievements = fs_get_u32(8)

def fs_save_achievements() -> None:
    global achievement_generation, achievement_slot
    if fs_ready == 0 or not ata_read_sector(13): return
    new_slot: i32 = 0 if achievement_slot == 1 else 1
    offset: i32 = new_slot * 16
    generation: i32 = achievement_generation + 1
    fs_buffer_set(offset, 65); fs_buffer_set(offset + 1, 67); fs_buffer_set(offset + 2, 1); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation); fs_put_u32(offset + 8, achievements)
    fs_put_u32(offset + 12, generation ^ achievements ^ 0x41434856)
    if ata_write_sector(13): achievement_generation = generation; achievement_slot = new_slot

def unlock_achievement(identifier: i32) -> None:
    global achievements, achievement_popup, achievement_popup_until
    bit: i32 = 1 << identifier
    if (achievements & bit) != 0: return
    achievements = achievements | bit
    achievement_popup = identifier
    achievement_popup_until = system_periods + 300
    fs_save_achievements()

def normal_achievement_count() -> i32:
    count: i32 = 0
    index: i32 = 0
    while index < 9:
        if (achievements & (1 << index)) != 0: count = count + 1
        index = index + 1
    return count
def stats_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 83 or fs_buffer_get(offset + 1) != 80:
        return False
    generation: i32 = fs_get_u32(offset + 4)
    play_time: i32 = fs_get_u32(offset + 8)
    lines: i32 = fs_get_u32(offset + 12)
    pieces: i32 = fs_get_u32(offset + 16)
    return fs_get_u32(offset + 20) == (generation ^ play_time ^ lines ^ pieces ^ 0x53544154)

def fs_load_statistics() -> None:
    global total_play_periods, total_lines, total_pieces, stats_generation, stats_slot
    total_play_periods = 0
    total_lines = 0
    total_pieces = 0
    stats_generation = 0
    stats_slot = 0
    if not ata_read_sector(12): return
    valid_a: bool = stats_record_valid(0)
    valid_b: bool = stats_record_valid(24)
    generation_a: i32 = fs_get_u32(4) if valid_a else -1
    generation_b: i32 = fs_get_u32(28) if valid_b else -1
    offset: i32 = 0
    if valid_b and generation_b > generation_a:
        stats_slot = 1
        stats_generation = generation_b
        offset = 24
    elif valid_a:
        stats_generation = generation_a
    else:
        return
    total_play_periods = fs_get_u32(offset + 8)
    total_lines = fs_get_u32(offset + 12)
    total_pieces = fs_get_u32(offset + 16)

def fs_save_statistics() -> None:
    global stats_generation, stats_slot
    if fs_ready == 0 or not ata_read_sector(12): return
    new_slot: i32 = 0 if stats_slot == 1 else 1
    offset: i32 = new_slot * 24
    generation: i32 = stats_generation + 1
    fs_buffer_set(offset, 83); fs_buffer_set(offset + 1, 80)
    fs_buffer_set(offset + 2, 1); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation)
    fs_put_u32(offset + 8, total_play_periods)
    fs_put_u32(offset + 12, total_lines)
    fs_put_u32(offset + 16, total_pieces)
    fs_put_u32(offset + 20, generation ^ total_play_periods ^ total_lines ^ total_pieces ^ 0x53544154)
    if ata_write_sector(12):
        stats_generation = generation
        stats_slot = new_slot
def combo_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 77 or fs_buffer_get(offset + 1) != 67:
        return False
    generation: i32 = fs_get_u32(offset + 4)
    saved_combo: i32 = fs_get_u32(offset + 8)
    return fs_get_u32(offset + 12) == (generation ^ saved_combo ^ 0x434F4D42)

def fs_load_max_combo() -> None:
    global max_combo, combo_generation, combo_slot
    max_combo = 0
    combo_generation = 0
    combo_slot = 0
    if not ata_read_sector(10):
        return
    valid_a: bool = combo_record_valid(0)
    valid_b: bool = combo_record_valid(16)
    generation_a: i32 = fs_get_u32(4) if valid_a else -1
    generation_b: i32 = fs_get_u32(20) if valid_b else -1
    if valid_b and generation_b > generation_a:
        combo_slot = 1
        combo_generation = generation_b
        max_combo = fs_get_u32(24)
    elif valid_a:
        combo_generation = generation_a
        max_combo = fs_get_u32(8)

def fs_save_max_combo(value: i32) -> None:
    global max_combo, combo_generation, combo_slot
    if value <= max_combo:
        return
    max_combo = value
    if fs_ready == 0 or not ata_read_sector(10):
        return
    new_slot: i32 = 0 if combo_slot == 1 else 1
    offset: i32 = new_slot * 16
    generation: i32 = combo_generation + 1
    fs_buffer_set(offset, 77); fs_buffer_set(offset + 1, 67)
    fs_buffer_set(offset + 2, 1); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation)
    fs_put_u32(offset + 8, value)
    fs_put_u32(offset + 12, generation ^ value ^ 0x434F4D42)
    if ata_write_sector(10):
        combo_generation = generation
        combo_slot = new_slot
