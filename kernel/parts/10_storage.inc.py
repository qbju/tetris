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
    if not ata_write_sector(13): return False
    fs_buffer_clear()
    if not ata_write_sector(14): return False
    fs_buffer_clear()
    return ata_write_sector(15)


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
    return fs_get_u32(offset + 32) == checksum and (saved_clock == 0 or saved_clock == 256 or saved_clock == 257 or (saved_clock >= 512 and saved_clock <= 515) or (saved_clock >= 1024 and saved_clock <= 1279)) and saved_colour >= 0 and saved_colour <= 5 and saved_gravity >= 10 and saved_gravity <= 100 and saved_control >= 0 and saved_control <= 1 and saved_bgm >= 0 and saved_bgm <= 10 and saved_se >= 0 and saved_se <= 10 and saved_debug >= 0 and saved_debug <= 1

def fs_load_settings() -> None:
    global color_mode, gravity_periods, control_mode, keyboard_layout, bgm_volume, se_volume, debug_enabled, clock_enabled, ghost_enabled, music_mode, settings_generation, settings_slot
    color_mode = 0
    gravity_periods = 50
    control_mode = 0
    keyboard_layout = 0
    bgm_volume = 6
    se_volume = 5
    debug_enabled = 1
    clock_enabled = 1
    ghost_enabled = 1
    music_mode = 0
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
    if saved_clock >= 1024:
        packed_options: i32 = saved_clock - 1024
        clock_enabled = packed_options & 1
        ghost_enabled = (packed_options >> 1) & 1
        music_mode = (packed_options >> 2) & 3
        keyboard_layout = (packed_options >> 4) & 15
        if keyboard_layout >= keyboard_layout_count(): keyboard_layout = 0
    elif saved_clock >= 512:
        packed_options = saved_clock - 512
        clock_enabled = packed_options & 1
        ghost_enabled = (packed_options >> 1) & 1
        music_mode = 0
    else:
        clock_enabled = saved_clock - 256 if saved_clock >= 256 else 1
        ghost_enabled = 1
        music_mode = 0

def fs_save_settings() -> None:
    global settings_generation, settings_slot
    if fs_ready == 0 or not ata_read_sector(9):
        return
    new_slot: i32 = 0 if settings_slot == 1 else 1
    offset: i32 = new_slot * 40
    generation: i32 = settings_generation + 1
    saved_clock: i32 = 1024 + clock_enabled + ghost_enabled * 2 + music_mode * 4 + keyboard_layout * 16
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
# Extension setting capability bits:
#   1 settings.read, 2 settings.write, 4 settings.save, 8 autostart
# Extension sources opt in with, for example:
#   # permissions: settings.read settings.write settings.save autostart
def fs_autostart_identifier() -> i32:
    if fs_ready == 0 or not ata_read_sector(15): return -1
    if fs_buffer_get(0) != 65 or fs_buffer_get(1) != 85 or fs_buffer_get(2) != 84 or fs_buffer_get(3) != 79: return -1
    if fs_buffer_get(4) != 1: return -1
    length: i32 = fs_buffer_get(5)
    if length <= 0 or length > 31: return -1
    checksum: i32 = 0x4155544F ^ length
    index: i32 = 0
    while index < length:
        checksum = checksum ^ (fs_buffer_get(8 + index) << (index & 3))
        index = index + 1
    if fs_get_u32(40) != checksum: return -1
    return extension_autostart_match(length)


def fs_set_autostart(identifier: i32, enabled: i32) -> i32:
    if fs_ready == 0: return -1
    fs_buffer_clear()
    if enabled != 0:
        length: i32 = extension_name_length(identifier)
        if length <= 0 or length > 31: return -2
        fs_buffer_set(0, 65); fs_buffer_set(1, 85); fs_buffer_set(2, 84); fs_buffer_set(3, 79)
        fs_buffer_set(4, 1); fs_buffer_set(5, length)
        checksum: i32 = 0x4155544F ^ length
        index: i32 = 0
        while index < length:
            character: i32 = extension_name_char(identifier, index)
            fs_buffer_set(8 + index, character)
            checksum = checksum ^ (character << (index & 3))
            index = index + 1
        fs_put_u32(40, checksum)
    if not ata_write_sector(15): return -3
    return 0


def extension_admin_set_autostart(identifier: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 2048) == 0: return -1
    if identifier < -1 or identifier >= extension_count(): return -2
    if identifier < 0: return fs_set_autostart(0, 0)
    if extension_background_capable(identifier) == 0: return -3
    return fs_set_autostart(identifier, 1)


def extension_admin_autostart_get() -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 2048) == 0: return -1
    return fs_autostart_identifier()


def extension_admin_permission_get(identifier: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 2048) == 0: return -1
    if identifier < 0 or identifier >= extension_count(): return -2
    return extension_permission_mask(identifier)


def extension_setting_get(key: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 1) == 0: return -1
    if key == 0: return color_mode
    if key == 1: return gravity_periods
    if key == 2: return control_mode
    if key == 3: return bgm_volume
    if key == 4: return se_volume
    if key == 5: return debug_enabled
    if key == 6: return clock_enabled
    if key == 7: return ghost_enabled
    if key == 8: return music_mode
    if key == 9: return keyboard_layout
    if key == 100:
        configured: i32 = fs_autostart_identifier()
        return 1 if configured == extension_current_id else 0
    return -2


def extension_setting_set(key: i32, value: i32) -> i32:
    global color_mode, gravity_periods, control_mode, keyboard_layout, bgm_volume, se_volume, debug_enabled, clock_enabled, ghost_enabled, music_mode
    if extension_current_id < 0: return -1
    if key == 100:
        if (extension_current_permissions & 8) == 0: return -3
        return fs_set_autostart(extension_current_id, value)
    if (extension_current_permissions & 2) == 0: return -3
    if key == 0:
        if value < 0 or value > 5: return -4
        color_mode = value
        vga_set_palette(color_mode)
    elif key == 1:
        if value < 10 or value > 100: return -4
        gravity_periods = value
    elif key == 2:
        if value < 0 or value > 1: return -4
        control_mode = value
    elif key == 3:
        if value < 0 or value > 10: return -4
        bgm_volume = value
    elif key == 4:
        if value < 0 or value > 10: return -4
        se_volume = value
    elif key == 5:
        if value < 0 or value > 1: return -4
        debug_enabled = value
    elif key == 6:
        if value < 0 or value > 1: return -4
        clock_enabled = value
    elif key == 7:
        if value < 0 or value > 1: return -4
        ghost_enabled = value
    elif key == 8:
        if value < 0 or value > 2: return -4
        music_mode = value
    elif key == 9:
        if value < 0 or value >= keyboard_layout_count(): return -4
        keyboard_layout = value
    else:
        return -2
    if (extension_current_permissions & 4) != 0: fs_save_settings()
    return 0

# Each extension receives a stable 500-byte sector selected from its filename
# hash. Sector headers detect the unlikely event of a hash-slot collision.
def extension_storage_prepare(create: i32) -> i32:
    key: i32 = extension_storage_key(extension_current_id)
    if key < 0 or fs_ready == 0: return -1
    lba: i32 = 256 + (key & 8191)
    if not ata_read_sector(lba): return -2
    valid_magic: bool = fs_buffer_get(0) == 69 and fs_buffer_get(1) == 88 and fs_buffer_get(2) == 83 and fs_buffer_get(3) == 84
    if valid_magic:
        if fs_get_u32(4) != key: return -5
        return lba
    if create == 0: return 0
    fs_buffer_clear()
    fs_buffer_set(0, 69); fs_buffer_set(1, 88); fs_buffer_set(2, 83); fs_buffer_set(3, 84)
    fs_put_u32(4, key)
    return lba


def extension_storage_get(index: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 256) == 0: return -1
    if index < 0 or index >= 500: return -3
    lba: i32 = extension_storage_prepare(0)
    if lba < 0: return lba
    if lba == 0: return 0
    return fs_buffer_get(12 + index)


def extension_storage_set(index: i32, value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    if index < 0 or index >= 500 or value < 0 or value > 255: return -3
    lba: i32 = extension_storage_prepare(1)
    if lba < 0: return lba
    fs_buffer_set(12 + index, value)
    return 0 if ata_write_sector(lba) else -2


def extension_storage_get_u32(index: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 256) == 0: return -1
    if index < 0 or index > 496: return -3
    lba: i32 = extension_storage_prepare(0)
    if lba < 0: return lba
    if lba == 0: return 0
    return fs_get_u32(12 + index)


def extension_storage_set_u32(index: i32, value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    if index < 0 or index > 496: return -3
    lba: i32 = extension_storage_prepare(1)
    if lba < 0: return lba
    fs_put_u32(12 + index, value)
    return 0 if ata_write_sector(lba) else -2


# High-level key/value storage. The 500-byte private payload is divided into
# 25 exact-name records: 15 key bytes, one length byte, and one i32 value.
def extension_storage_kv_validate(key: str) -> i32:
    length: i32 = len(key)
    if length <= 0 or length > 15: return -1
    index: i32 = 0
    while index < length:
        character: i32 = ord(key[index])
        if character < 32 or character > 126: return -1
        index = index + 1
    return length


def extension_storage_kv_find(key: str) -> i32:
    length: i32 = extension_storage_kv_validate(key)
    if length < 0: return -3
    slot: i32 = 0
    while slot < 25:
        offset: i32 = 12 + slot * 20
        stored_length: i32 = fs_buffer_get(offset + 15)
        if stored_length == length:
            same: bool = True
            index: i32 = 0
            while same and index < length:
                if fs_buffer_get(offset + index) != ord(key[index]): same = False
                index = index + 1
            if same: return slot
        slot = slot + 1
    return -1


def extension_storage_kv_get(key: str, default_value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 256) == 0: return -1
    if extension_storage_kv_validate(key) < 0: return -3
    lba: i32 = extension_storage_prepare(0)
    if lba < 0: return lba
    if lba == 0: return default_value
    slot: i32 = extension_storage_kv_find(key)
    if slot < 0: return default_value
    return fs_get_u32(12 + slot * 20 + 16)


def extension_storage_kv_has(key: str) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 256) == 0: return -1
    if extension_storage_kv_validate(key) < 0: return -3
    lba: i32 = extension_storage_prepare(0)
    if lba < 0: return lba
    if lba == 0: return 0
    return 1 if extension_storage_kv_find(key) >= 0 else 0


def extension_storage_kv_set(key: str, value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    length: i32 = extension_storage_kv_validate(key)
    if length < 0: return -3
    lba: i32 = extension_storage_prepare(1)
    if lba < 0: return lba
    slot: i32 = extension_storage_kv_find(key)
    if slot < 0:
        slot = 0
        while slot < 25 and fs_buffer_get(12 + slot * 20 + 15) != 0:
            slot = slot + 1
        if slot >= 25: return -6
    offset: i32 = 12 + slot * 20
    index: i32 = 0
    while index < 15:
        fs_buffer_set(offset + index, ord(key[index]) if index < length else 0)
        index = index + 1
    fs_buffer_set(offset + 15, length)
    fs_put_u32(offset + 16, value)
    return 0 if ata_write_sector(lba) else -2


def extension_storage_kv_delete(key: str) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    if extension_storage_kv_validate(key) < 0: return -3
    lba: i32 = extension_storage_prepare(0)
    if lba < 0: return lba
    if lba == 0: return 0
    slot: i32 = extension_storage_kv_find(key)
    if slot < 0: return 0
    offset: i32 = 12 + slot * 20
    index: i32 = 0
    while index < 20:
        fs_buffer_set(offset + index, 0)
        index = index + 1
    return 0 if ata_write_sector(lba) else -2


# Multi-sector .KV format. This is separate from the compact 500-byte store.
# Each extension owns one virtual NAME.KV area of eight sectors: one header
# plus seven data sectors containing 16 fixed records each (112 total).
def extension_kvfile_prepare(create: i32) -> i32:
    key: i32 = extension_storage_key(extension_current_id)
    if key < 0 or fs_ready == 0: return -1
    base_lba: i32 = 16384 + (key & 2047) * 8
    if not ata_read_sector(base_lba): return -2
    valid_magic: bool = fs_buffer_get(0) == 75 and fs_buffer_get(1) == 86 and fs_buffer_get(2) == 70 and fs_buffer_get(3) == 49
    if valid_magic:
        if fs_get_u32(4) != key: return -5
        return base_lba
    if create == 0: return 0
    fs_buffer_clear()
    fs_buffer_set(0, 75); fs_buffer_set(1, 86); fs_buffer_set(2, 70); fs_buffer_set(3, 49)
    fs_put_u32(4, key)
    fs_buffer_set(8, 1)
    fs_buffer_set(9, 23)
    fs_buffer_set(10, 112)
    if not ata_write_sector(base_lba): return -2
    page: i32 = 1
    while page < 8:
        fs_buffer_clear()
        if not ata_write_sector(base_lba + page): return -2
        page = page + 1
    return base_lba


def extension_kvfile_validate(key: str) -> i32:
    length: i32 = len(key)
    if length <= 0 or length > 23: return -1
    index: i32 = 0
    while index < length:
        character: i32 = ord(key[index])
        if character < 32 or character > 126: return -1
        index = index + 1
    return length


def extension_kvfile_find(base_lba: i32, key: str) -> i32:
    length: i32 = extension_kvfile_validate(key)
    if length < 0: return -3
    page: i32 = 0
    while page < 7:
        if not ata_read_sector(base_lba + 1 + page): return -2
        record: i32 = 0
        while record < 16:
            offset: i32 = record * 32
            stored_length: i32 = fs_buffer_get(offset + 23)
            if stored_length == length:
                same: bool = True
                index: i32 = 0
                while same and index < length:
                    if fs_buffer_get(offset + index) != ord(key[index]): same = False
                    index = index + 1
                if same: return page * 16 + record
            record = record + 1
        page = page + 1
    return -1


def extension_kvfile_get(key: str, default_value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 256) == 0: return -1
    if extension_kvfile_validate(key) < 0: return -3
    base_lba: i32 = extension_kvfile_prepare(0)
    if base_lba < 0: return base_lba
    if base_lba == 0: return default_value
    slot: i32 = extension_kvfile_find(base_lba, key)
    if slot == -1: return default_value
    if slot < 0: return slot
    offset: i32 = (slot % 16) * 32
    value: i32 = fs_get_u32(offset + 24)
    if fs_get_u32(offset + 28) != (value ^ extension_storage_key(extension_current_id)): return -7
    return value


def extension_kvfile_has(key: str) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 256) == 0: return -1
    if extension_kvfile_validate(key) < 0: return -3
    base_lba: i32 = extension_kvfile_prepare(0)
    if base_lba < 0: return base_lba
    if base_lba == 0: return 0
    slot: i32 = extension_kvfile_find(base_lba, key)
    if slot < -1: return slot
    return 1 if slot >= 0 else 0


def extension_kvfile_set(key: str, value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    length: i32 = extension_kvfile_validate(key)
    if length < 0: return -3
    base_lba: i32 = extension_kvfile_prepare(1)
    if base_lba < 0: return base_lba
    slot: i32 = extension_kvfile_find(base_lba, key)
    if slot < -1: return slot
    if slot < 0:
        page: i32 = 0
        while page < 7 and slot < 0:
            if not ata_read_sector(base_lba + 1 + page): return -2
            record: i32 = 0
            while record < 16 and slot < 0:
                if fs_buffer_get(record * 32 + 23) == 0: slot = page * 16 + record
                record = record + 1
            page = page + 1
        if slot < 0: return -6
    page = slot // 16
    if not ata_read_sector(base_lba + 1 + page): return -2
    offset: i32 = (slot % 16) * 32
    index: i32 = 0
    while index < 23:
        fs_buffer_set(offset + index, ord(key[index]) if index < length else 0)
        index = index + 1
    fs_buffer_set(offset + 23, length)
    fs_put_u32(offset + 24, value)
    fs_put_u32(offset + 28, value ^ extension_storage_key(extension_current_id))
    return 0 if ata_write_sector(base_lba + 1 + page) else -2


def extension_kvfile_delete(key: str) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    if extension_kvfile_validate(key) < 0: return -3
    base_lba: i32 = extension_kvfile_prepare(0)
    if base_lba < 0: return base_lba
    if base_lba == 0: return 0
    slot: i32 = extension_kvfile_find(base_lba, key)
    if slot == -1: return 0
    if slot < 0: return slot
    page: i32 = slot // 16
    if not ata_read_sector(base_lba + 1 + page): return -2
    offset: i32 = (slot % 16) * 32
    index: i32 = 0
    while index < 32:
        fs_buffer_set(offset + index, 0)
        index = index + 1
    return 0 if ata_write_sector(base_lba + 1 + page) else -2


def extension_storage_clear() -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 512) == 0: return -1
    key: i32 = extension_storage_key(extension_current_id)
    if key < 0 or fs_ready == 0: return -1
    lba: i32 = 256 + (key & 8191)
    fs_buffer_clear()
    fs_buffer_set(0, 69); fs_buffer_set(1, 88); fs_buffer_set(2, 83); fs_buffer_set(3, 84)
    fs_put_u32(4, key)
    return 0 if ata_write_sector(lba) else -2

def fs_reset_data() -> None:
    global high_score, high_generation, high_slot, color_mode, gravity_periods, settings_generation, settings_slot, control_mode, keyboard_layout, bgm_volume, se_volume, debug_enabled, clock_enabled, ghost_enabled, music_mode, max_combo, combo_generation, combo_slot, total_play_periods, total_lines, total_pieces, stats_generation, stats_slot, achievements, achievement_generation, achievement_slot
    high_score = 0
    high_generation = 0
    high_slot = 0
    color_mode = 0
    gravity_periods = 50
    control_mode = 0
    keyboard_layout = 0
    bgm_volume = 6
    se_volume = 5
    debug_enabled = 1
    clock_enabled = 1
    ghost_enabled = 1
    music_mode = 0
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
    fs_buffer_clear()
    ata_write_sector(15)

def any_music_record_valid(offset: i32) -> bool:
    if fs_buffer_get(offset) != 65 or fs_buffer_get(offset + 1) != 77: return False
    generation: i32 = fs_get_u32(offset + 4)
    checksum: i32 = generation ^ 0x414E594D
    index: i32 = 0
    while index < 32:
        checksum = checksum ^ fs_get_u32(offset + 8 + index * 4)
        index = index + 1
    index = 0
    while index < 8:
        checksum = checksum ^ fs_buffer_get(offset + 136 + index)
        index = index + 1
    return fs_get_u32(offset + 144) == checksum

def fs_load_any_music() -> None:
    global any_music_generation, any_music_slot, music_name_length
    any_music_generation = 0
    any_music_slot = 0
    if not ata_read_sector(14):
        any_music_reset()
        return
    valid_a: bool = any_music_record_valid(0)
    valid_b: bool = any_music_record_valid(160)
    generation_a: i32 = fs_get_u32(4) if valid_a else -1
    generation_b: i32 = fs_get_u32(164) if valid_b else -1
    offset: i32 = 0
    if valid_b and generation_b > generation_a:
        offset = 160
        any_music_slot = 1
        any_music_generation = generation_b
    elif valid_a:
        any_music_generation = generation_a
    else:
        any_music_reset()
        return
    index: i32 = 0
    while index < 32:
        any_note_set(index, fs_get_u32(offset + 8 + index * 4))
        index = index + 1
    music_name_length = 0
    while music_name_length < 8 and fs_buffer_get(offset + 136 + music_name_length) != 0:
        any_name_set(music_name_length, fs_buffer_get(offset + 136 + music_name_length))
        music_name_length = music_name_length + 1
    index = music_name_length
    while index < 8:
        any_name_set(index, 0)
        index = index + 1

def fs_save_any_music() -> None:
    global any_music_generation, any_music_slot
    if fs_ready == 0 or not ata_read_sector(14): return
    new_slot: i32 = 0 if any_music_slot == 1 else 1
    offset: i32 = new_slot * 160
    generation: i32 = any_music_generation + 1
    checksum: i32 = generation ^ 0x414E594D
    fs_buffer_set(offset, 65); fs_buffer_set(offset + 1, 77); fs_buffer_set(offset + 2, 1); fs_buffer_set(offset + 3, 0)
    fs_put_u32(offset + 4, generation)
    index: i32 = 0
    while index < 32:
        packed_note: i32 = any_note_get(index)
        fs_put_u32(offset + 8 + index * 4, packed_note)
        checksum = checksum ^ packed_note
        index = index + 1
    index = 0
    while index < 8:
        name_character: i32 = any_name_get(index)
        fs_buffer_set(offset + 136 + index, name_character)
        checksum = checksum ^ name_character
        index = index + 1
    fs_put_u32(offset + 144, checksum)
    if ata_write_sector(14):
        any_music_generation = generation
        any_music_slot = new_slot
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
    fs_load_any_music()
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
def non_hidden_achievement_count() -> i32:
    count: i32 = 0
    identifier: i32 = 0
    while identifier < 24:
        if (identifier < 9 or identifier > 13) and (achievements & (1 << identifier)) != 0:
            count = count + 1
        identifier = identifier + 1
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
