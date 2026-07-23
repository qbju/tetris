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
extension_selection: i32 = 0
extension_active: i32 = 0
ui_transition_active: i32 = 0
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
game_mode: i32 = 0  # 0 = ENDLESS, 1 = MARATHON 150, 2 = SPRINT 40
sprint_lines: i32 = 0
sprint_start_period: i32 = 0
sprint_elapsed_periods: i32 = 0
session_hold_used: i32 = 0
last_action_rotation: i32 = 0
session_tspins: i32 = 0
survivor_start_period: i32 = 0
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

def extension_draw_text(x: i32, y: i32, message: str, colour: i32) -> i32:
    length: i32 = len(message)
    available: i32 = 80 - x
    draw_length: i32 = length if length < available else available
    if x < 0 or y < 0 or y >= 25 or available <= 0: return 0
    index: i32 = 0
    while index < draw_length:
        text(x + index, y, ord(message[index]), colour)
        index = index + 1
    return draw_length


def extension_draw_text_centered(y: i32, message: str, colour: i32) -> i32:
    length: i32 = len(message)
    visible_length: i32 = length if length <= 80 else 80
    return extension_draw_text((80 - visible_length) // 2, y, message, colour)

def extension_native_fill_rect(x: i32, y: i32, width: i32, height: i32, colour: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 1024) == 0: return -1
    ui_native_fill_rect(x, y, width, height, colour)
    return 0


def extension_native_draw_text(x: i32, y: i32, message: str, colour: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 1024) == 0: return -1
    length: i32 = len(message)
    available: i32 = (640 - x) // 8
    draw_length: i32 = length if length < available else available
    if x < 0 or y < 0 or y >= 480 or available <= 0: return 0
    index: i32 = 0
    while index < draw_length:
        ui_native_put_cell(x + index * 8, y, ord(message[index]), colour)
        index = index + 1
    return draw_length

def extension_letterbox_fill(bar: i32, colour: i32) -> None:
    physical_y: i32 = 0 if bar == 0 else 440
    ui_letterbox_fill_rect(0, physical_y, 640, 40, colour)


def extension_letterbox_draw_text(bar: i32, row: i32, x: i32, message: str, colour: i32) -> i32:
    if bar < 0 or bar > 1 or row < 0 or row > 1 or x < 0 or x >= 80: return 0
    length: i32 = len(message)
    available: i32 = 80 - x
    draw_length: i32 = length if length < available else available
    physical_y: i32 = 4 + row * 16 if bar == 0 else 444 + row * 16
    index: i32 = 0
    while index < draw_length:
        ui_letterbox_put_cell((x + index) * 8, physical_y, ord(message[index]), colour)
        index = index + 1
    return draw_length


def extension_letterbox_clear() -> None:
    extension_letterbox_fill(0, 0)
    extension_letterbox_fill(1, 0)

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


def achievement_chunk(identifier: i32, group: i32) -> i32:
    if identifier == 0:
        if group == 0: return 1397901638
        if group == 1: return 1279402068
        if group == 2: return 4932431
    elif identifier == 1:
        if group == 0: return 1162758476
        if group == 1: return 1162759968
    elif identifier == 2:
        if group == 0: return 1381322566
        if group == 1: return 1145657120
        if group == 2: return 69
    elif identifier == 3:
        if group == 0: return 1414808903
        if group == 1: return 541544009
        if group == 2: return 1380013139
        if group == 3: return 4474196
    elif identifier == 4:
        if group == 0: return 1163282758
        if group == 1: return 1195983904
        if group == 2: return 5461065
    elif identifier == 5:
        if group == 0: return 1414415683
        if group == 1: return 5853781
    elif identifier == 6:
        if group == 0: return 1095909709
        if group == 1: return 1313818708
    elif identifier == 7:
        if group == 0: return 1112362819
        if group == 1: return 1414733903
        if group == 2: return 1163153985
        if group == 3: return 82
    elif identifier == 8:
        if group == 0: return 1229015107
        if group == 1: return 1163010126
        if group == 2: return 1230259009
        if group == 3: return 20047
    elif identifier == 9:
        if group == 0: return 1428181077
        if group == 1: return 1329864784
        if group == 2: return 1142967895
        if group == 3: return 5134159
    elif identifier == 10:
        if group == 0: return 1162627411
        if group == 1: return 1377850446
        if group == 2: return 20053
    elif identifier == 11:
        if group == 0: return 541346895
        if group == 1: return 1330135891
        if group == 2: return 19535
    elif identifier == 12:
        if group == 0: return 1095189838
        if group == 1: return 1163282772
        if group == 2: return 1095783200
        if group == 3: return 17731
    elif identifier == 13:
        if group == 0: return 1330662729
        if group == 1: return 1112101715
        if group == 2: return 17740
    elif identifier == 14:
        if group == 0: return 1397901638
        if group == 1: return 1313153108
        if group == 2: return 1397050436
        if group == 3: return 83
    elif identifier == 15:
        if group == 0: return 1397901638
        if group == 1: return 1095573588
        if group == 2: return 1213481298
        if group == 3: return 20047
    elif identifier == 16:
        if group == 0: return 1397901638
        if group == 1: return 1347625044
        if group == 2: return 1414416722
    elif identifier == 17:
        if group == 0: return 1330138958
        if group == 1: return 1293960268
        if group == 2: return 1413567041
        if group == 3: return 5132104
    elif identifier == 18:
        if group == 0: return 1330138958
        if group == 1: return 1394623564
        if group == 2: return 1313428048
        if group == 3: return 84
    elif identifier == 19:
        if group == 0: return 1179796816
        if group == 1: return 542393157
        if group == 2: return 1128354899
        if group == 3: return 75
    elif identifier == 20:
        if group == 0: return 1397704775
        if group == 1: return 1397050452
        if group == 2: return 83
    elif identifier == 21:
        if group == 0: return 1448236371
        if group == 1: return 1380931145
    elif identifier == 22:
        if group == 0: return 1347628372
        if group == 1: return 1380273737
    elif identifier == 23:
        if group == 0: return 1347628372
        if group == 1: return 1293962825
        if group == 2: return 1163154241
        if group == 3: return 82
    return 0
def draw_achievement_title(identifier: i32, x: i32, y: i32, colour: i32) -> None:
    position: i32 = 0
    while position < 16:
        packed: i32 = achievement_chunk(identifier, position // 4)
        character: i32 = (packed >> ((position % 4) * 8)) & 255
        if character != 0: text(x + position, y, character, colour)
        position = position + 1

def draw_extension_notification() -> None:
    if extension_notification_source < 0 or system_periods >= extension_notification_until: return
    y: i32 = 16
    while y < 20:
        x: i32 = 53
        while x < 79:
            ui_put_cell(x, y, 32, 0x30)
            x = x + 1
        y = y + 1
    # APP: <extension filename>
    text(55, 16, 65, 0x3E); text(56, 16, 80, 0x3E); text(57, 16, 80, 0x3E); text(58, 16, 58, 0x3E)
    name_length: i32 = extension_name_length(extension_notification_source)
    if name_length > 17: name_length = 17
    index: i32 = 0
    while index < name_length:
        text(60 + index, 16, extension_name_char(extension_notification_source, index), 0x3F)
        index = index + 1
    index = 0
    while index < extension_notification_length:
        text(55 + index, 18, extension_memory_get(976 + index), extension_notification_colour)
        index = index + 1

def draw_achievement_popup() -> None:
    if achievement_popup < 0 or system_periods >= achievement_popup_until: return
    y: i32 = 20
    while y < 24:
        x: i32 = 54
        while x < 79:
            ui_put_cell(x, y, 32, 0x60)
            x = x + 1
        y = y + 1
    text(56, 20, 65, 0x6E); text(57, 20, 67, 0x6E); text(58, 20, 72, 0x6E); text(59, 20, 73, 0x6E); text(60, 20, 69, 0x6E); text(61, 20, 86, 0x6E); text(62, 20, 69, 0x6E); text(63, 20, 77, 0x6E); text(64, 20, 69, 0x6E); text(65, 20, 78, 0x6E); text(66, 20, 84, 0x6E)
    draw_achievement_title(achievement_popup, 56, 22, 0x6F)

def achievement_description_chunk(identifier: i32, group: i32) -> i32:
    if identifier == 0:
        if group == 0: return 1128352848
        if group == 1: return 1331241029
        if group == 2: return 1176523349
        if group == 3: return 1414746697
        if group == 4: return 1413829664
        if group == 5: return 1229803346
        if group == 6: return 20302
    elif identifier == 1:
        if group == 0: return 1095060547
        if group == 1: return 1331241042
        if group == 2: return 1176523349
        if group == 3: return 1414746697
        if group == 4: return 1313426464
        if group == 5: return 69
    elif identifier == 2:
        if group == 0: return 1095060547
        if group == 1: return 1329995858
        if group == 2: return 1277186645
        if group == 3: return 1397050953
        if group == 4: return 542392608
        if group == 5: return 1162038863
    elif identifier == 3:
        if group == 0: return 1128352848
        if group == 1: return 808525893
        if group == 2: return 1163141168
        if group == 3: return 1297044052
        if group == 4: return 1162825289
        if group == 5: return 83
    elif identifier == 4:
        if group == 0: return 1128351058
        if group == 1: return 541139016
        if group == 2: return 1380926291
        if group == 3: return 1179590725
        if group == 4: return 808464672
        if group == 5: return 12336
    elif identifier == 5:
        if group == 0: return 1095060547
        if group == 1: return 808525906
        if group == 2: return 1229725744
        if group == 3: return 542328142
        if group == 4: return 1411403337
        if group == 5: return 1279349839
    elif identifier == 6:
        if group == 0: return 1497451600
        if group == 1: return 1380927008
        if group == 2: return 1162759968
        if group == 3: return 1431259168
        if group == 4: return 1313415250
        if group == 5: return 1414485024
        if group == 6: return 19521
    elif identifier == 7:
        if group == 0: return 1128351058
        if group == 1: return 541139016
        if group == 2: return 1329799219
        if group == 3: return 5194317
    elif identifier == 8:
        if group == 0: return 1128351058
        if group == 1: return 1312890952
        if group == 2: return 1126184992
        if group == 3: return 1329745231
    elif identifier == 9:
        if group == 0: return 1163152965
        if group == 1: return 1213472850
        if group == 2: return 1163075653
        if group == 3: return 1413829187
        if group == 4: return 1146045216
        if group == 5: return 1413554245
        if group == 6: return 1297041440
        if group == 7: return 69
    elif identifier == 10:
        if group == 0: return 1229867334
        if group == 1: return 1092634707
        if group == 2: return 1296123680
        if group == 3: return 1230446661
        if group == 4: return 1109411924
        if group == 5: return 1092635975
        if group == 6: return 1394623566
        if group == 7: return 1431117893
        if group == 8: return 4474196
    elif identifier == 11:
        if group == 0: return 1095060547
        if group == 1: return 808525906
        if group == 2: return 1313426464
        if group == 3: return 1226855237
        if group == 4: return 1380393038
        if group == 5: return 1129535809
        if group == 6: return 4541505
    elif identifier == 12:
        if group == 0: return 1380926291
        if group == 1: return 808525893
        if group == 2: return 1226846256
        if group == 3: return 1313415246
        if group == 4: return 1414677846
        if group == 5: return 1146047776
        if group == 6: return 69
    elif identifier == 13:
        if group == 0: return 1111576133
        if group == 1: return 1411401036
        if group == 2: return 1210074440
        if group == 3: return 1162101833
        if group == 4: return 1430397006
        if group == 5: return 541346889
        if group == 6: return 1195461702
    elif identifier == 14:
        if group == 0: return 1380013139
        if group == 1: return 1313153108
        if group == 2: return 1397050436
        if group == 3: return 1330454611
        if group == 4: return 17732
    elif identifier == 15:
        if group == 0: return 1380013139
        if group == 1: return 1095573588
        if group == 2: return 1213481298
        if group == 3: return 1293962831
        if group == 4: return 4539471
    elif identifier == 16:
        if group == 0: return 1380013139
        if group == 1: return 1347625044
        if group == 2: return 1414416722
        if group == 3: return 540029984
        if group == 4: return 1162104653
    elif identifier == 17:
        if group == 0: return 1229867334
        if group == 1: return 1293961299
        if group == 2: return 1413567041
        if group == 3: return 542003016
        if group == 4: return 1213483351
        if group == 5: return 542397775
        if group == 6: return 1145851720
    elif identifier == 18:
        if group == 0: return 1229867334
        if group == 1: return 1394624595
        if group == 2: return 1313428048
        if group == 3: return 1230446676
        if group == 4: return 1431259220
        if group == 5: return 1330126932
        if group == 6: return 17484
    elif identifier == 19:
        if group == 0: return 1095060547
        if group == 1: return 1213472850
        if group == 2: return 1313153093
        if group == 3: return 1163020628
        if group == 4: return 1095713312
        if group == 5: return 17490
    elif identifier == 20:
        if group == 0: return 1380926291
        if group == 1: return 1448026181
        if group == 2: return 824201797
        if group == 3: return 540028976
        if group == 4: return 1213483351
        if group == 5: return 1330136864
        if group == 6: return 1327518803
        if group == 7: return 17990
    elif identifier == 21:
        if group == 0: return 1448236371
        if group == 1: return 541414985
        if group == 2: return 1229791285
        if group == 3: return 1413554254
        if group == 4: return 808465184
        if group == 5: return 1327518541
        if group == 6: return 1162616914
        if group == 7: return 21331
    elif identifier == 22:
        if group == 0: return 1179796816
        if group == 1: return 541938255
        if group == 2: return 541412943
        if group == 3: return 1347628372
        if group == 4: return 20041
    elif identifier == 23:
        if group == 0: return 1179796816
        if group == 1: return 541938255
        if group == 2: return 1163282758
        if group == 3: return 1395479584
        if group == 4: return 1397639504
    return 0

def draw_achievement_detail() -> None:
    y: i32 = 5
    while y < 20:
        x: i32 = 12
        while x < 68:
            ui_put_cell(x, y, 32, 0x50)
            x = x + 1
        y = y + 1
    x = 12
    while x < 68:
        ui_put_cell(x, 5, 205, 0x5F); ui_put_cell(x, 19, 205, 0x5F)
        x = x + 1
    y = 6
    while y < 19:
        ui_put_cell(12, y, 186, 0x5F); ui_put_cell(67, y, 186, 0x5F)
        y = y + 1
    ui_put_cell(12, 5, 201, 0x5F); ui_put_cell(67, 5, 187, 0x5F)
    ui_put_cell(12, 19, 200, 0x5F); ui_put_cell(67, 19, 188, 0x5F)
    unlocked: i32 = 1 if (achievements & (1 << achievement_selection)) != 0 else 0
    if achievement_selection >= 9 and achievement_selection <= 13 and unlocked == 0:
        text(31, 8, 72, 0x58); text(32, 8, 73, 0x58); text(33, 8, 68, 0x58); text(34, 8, 68, 0x58); text(35, 8, 69, 0x58); text(36, 8, 78, 0x58)
        # UNLOCK TO REVEAL DETAILS
        hidden_message: i32 = 0
        while hidden_message < 24:
            hidden_packed: i32 = 1330400853 if hidden_message // 4 == 0 else (1411395403 if hidden_message // 4 == 1 else (1163282258 if hidden_message // 4 == 2 else (1279349836 if hidden_message // 4 == 3 else (1096040773 if hidden_message // 4 == 4 else 5458252))))
            hidden_character: i32 = (hidden_packed >> ((hidden_message % 4) * 8)) & 255
            if hidden_character != 0: text(27 + hidden_message, 13, hidden_character, 0x57)
            hidden_message = hidden_message + 1
    else:
        draw_achievement_title(achievement_selection, 20, 8, 0x5F)
        position: i32 = 0
        while position < 48:
            description_packed: i32 = achievement_description_chunk(achievement_selection, position // 4)
            description_character: i32 = (description_packed >> ((position % 4) * 8)) & 255
            if description_character != 0: text(16 + position, 13, description_character, 0x5F)
            position = position + 1
        if unlocked == 1:
            text(31, 16, 85, 0x5A); text(32, 16, 78, 0x5A); text(33, 16, 76, 0x5A); text(34, 16, 79, 0x5A); text(35, 16, 67, 0x5A); text(36, 16, 75, 0x5A); text(37, 16, 69, 0x5A); text(38, 16, 68, 0x5A)
        else:
            text(32, 16, 76, 0x58); text(33, 16, 79, 0x58); text(34, 16, 67, 0x58); text(35, 16, 75, 0x58); text(36, 16, 69, 0x58); text(37, 16, 68, 0x58)
    text(26, 18, 69, 0x57); text(27, 18, 78, 0x57); text(28, 18, 84, 0x57); text(29, 18, 69, 0x57); text(30, 18, 82, 0x57)
    text(32, 18, 79, 0x57); text(33, 18, 82, 0x57); text(35, 18, 69, 0x57); text(36, 18, 83, 0x57); text(37, 18, 67, 0x57)
def draw_achievements() -> None:
    draw_menu()
    y: i32 = 4
    while y < 22:
        x: i32 = 14
        while x < 66:
            ui_put_cell(x, y, 32, 0x50)
            x = x + 1
        y = y + 1
    start: i32 = achievement_page * 7
    index: i32 = 0
    while index < 7 and start + index < 24:
        identifier: i32 = start + index
        row: i32 = 6 + index * 2
        unlocked: i32 = 1 if (achievements & (1 << identifier)) != 0 else 0
        text(15, row, 16 if identifier == achievement_selection else 32, 0x5E)
        text(17, row, 43 if unlocked == 1 else 45, 0x5A if unlocked == 1 else 0x58)
        if identifier >= 9 and identifier <= 13 and unlocked == 0:
            text(21, row, 72, 0x58); text(22, row, 73, 0x58); text(23, row, 68, 0x58); text(24, row, 68, 0x58); text(25, row, 69, 0x58); text(26, row, 78, 0x58)
        else:
            draw_achievement_title(identifier, 21, row, 0x5F if unlocked == 1 else 0x57)
        index = index + 1
    text(31, 20, 76, 0x5F); text(32, 20, 69, 0x5F); text(33, 20, 70, 0x5F); text(34, 20, 84, 0x5F)
    text(36, 20, 82, 0x5F); text(37, 20, 73, 0x5F); text(38, 20, 71, 0x5F); text(39, 20, 72, 0x5F); text(40, 20, 84, 0x5F)
    if achievement_detail_open == 1: draw_achievement_detail()
def update_konami(key: i32) -> None:
    global konami_progress, menu_drawn
    if key == 0: return
    expected: i32 = 0x48
    if konami_progress == 2 or konami_progress == 3: expected = 0x50
    elif konami_progress == 4 or konami_progress == 6: expected = 0x4B
    elif konami_progress == 5 or konami_progress == 7: expected = 0x4D
    elif konami_progress == 8: expected = 0x30
    elif konami_progress == 9: expected = 0x1E
    if key == expected:
        konami_progress = konami_progress + 1
        if konami_progress >= 10:
            konami_progress = 0
            unlock_achievement(9)
            sound_sequence(1193, 5, 948, 5, 710, 8, 3)
            menu_drawn = 0
    else:
        konami_progress = 1 if key == 0x48 else 0

def draw_build_info() -> None:
    draw_statistics()
    # Erase statistics values before BUILD INFO (including the stale seconds suffix).
    clear_y: i32 = 10
    while clear_y < 18:
        clear_x: i32 = 22
        while clear_x < 58:
            ui_put_cell(clear_x, clear_y, 32, 0x30)
            clear_x = clear_x + 1
        clear_y = clear_y + 1
    text(32, 8, 66, 0x3F); text(33, 8, 85, 0x3F); text(34, 8, 73, 0x3F); text(35, 8, 76, 0x3F); text(36, 8, 68, 0x3F)
    text(38, 8, 73, 0x3F); text(39, 8, 78, 0x3F); text(40, 8, 70, 0x3F); text(41, 8, 79, 0x3F)
    text(24, 11, 76, 0x3B); text(25, 11, 80, 0x3B); text(26, 11, 89, 0x3B); text(27, 11, 84, 0x3B); text(28, 11, 72, 0x3B); text(29, 11, 79, 0x3B); text(30, 11, 78, 0x3B)
    text(45, 11, 76, 0x3F); text(46, 11, 76, 0x3F); text(47, 11, 86, 0x3F); text(48, 11, 77, 0x3F)
    text(24, 13, 84, 0x3B); text(25, 13, 65, 0x3B); text(26, 13, 82, 0x3B); text(27, 13, 71, 0x3B); text(28, 13, 69, 0x3B); text(29, 13, 84, 0x3B)
    text(45, 13, 73, 0x3F); text(46, 13, 51, 0x3F); text(47, 13, 56, 0x3F); text(48, 13, 54, 0x3F)
    text(24, 15, 66, 0x3B); text(25, 15, 85, 0x3B); text(26, 15, 73, 0x3B); text(27, 15, 76, 0x3B); text(28, 15, 68, 0x3B)
    text(45, 15, 68, 0x3F); text(46, 15, 69, 0x3F); text(47, 15, 86, 0x3F)
def draw_extensions() -> None:
    draw_menu()
    y: i32 = 5
    while y < 21:
        x: i32 = 14
        while x < 66:
            ui_put_cell(x, y, 32, 0x30)
            x = x + 1
        y = y + 1
    text(31, 6, 69, 0x3F); text(32, 6, 88, 0x3F); text(33, 6, 84, 0x3F); text(34, 6, 69, 0x3F); text(35, 6, 78, 0x3F); text(36, 6, 83, 0x3F); text(37, 6, 73, 0x3F); text(38, 6, 79, 0x3F); text(39, 6, 78, 0x3F); text(40, 6, 83, 0x3F)
    count: i32 = extension_count()
    first: i32 = extension_selection - 4 if extension_selection >= 5 else 0
    row_index: i32 = 0
    while row_index < 6 and first + row_index < count:
        identifier: i32 = first + row_index
        row: i32 = 9 + row_index * 2
        text(17, row, 16 if identifier == extension_selection else 32, 0x3E)
        length: i32 = extension_name_length(identifier)
        position: i32 = 0
        while position < length and position < 42:
            text(20 + position, row, extension_name_char(identifier, position), 0x3F if identifier == extension_selection else 0x37)
            position = position + 1
        row_index = row_index + 1
    text(25, 22, 85, 0x37); text(26, 22, 80, 0x37); text(28, 22, 68, 0x37); text(29, 22, 79, 0x37); text(30, 22, 87, 0x37)
    text(34, 22, 69, 0x3A); text(35, 22, 78, 0x3A); text(36, 22, 84, 0x3A); text(37, 22, 69, 0x3A); text(38, 22, 82, 0x3A)
    text(42, 22, 69, 0x37); text(43, 22, 83, 0x37); text(44, 22, 67, 0x37); text(46, 22, 66, 0x37); text(47, 22, 65, 0x37); text(48, 22, 67, 0x37); text(49, 22, 75, 0x37)
def draw_menu_label(item: i32, y: i32) -> None:
    colour: i32 = 0x2F if menu_selection == item else 0x1F
    if item == 0:
        text(31, y, 80, colour); text(32, y, 76, colour); text(33, y, 65, colour); text(34, y, 89, colour)
        if game_mode == 0:
            text(36, y, 69, colour); text(37, y, 78, colour); text(38, y, 68, colour); text(39, y, 76, colour); text(40, y, 69, colour); text(41, y, 83, colour); text(42, y, 83, colour)
        elif game_mode == 1:
            text(36, y, 77, colour); text(37, y, 65, colour); text(38, y, 82, colour); text(39, y, 65, colour); text(40, y, 84, colour); text(41, y, 72, colour); text(42, y, 79, colour); text(43, y, 78, colour)
        else:
            text(36, y, 83, colour); text(37, y, 80, colour); text(38, y, 82, colour); text(39, y, 73, colour); text(40, y, 78, colour); text(41, y, 84, colour); text(42, y, 32, colour); text(43, y, 52, colour); text(44, y, 48, colour)
    elif item == 1:
        text(35, y, 83, colour); text(36, y, 69, colour); text(37, y, 84, colour); text(38, y, 84, colour); text(39, y, 73, colour); text(40, y, 78, colour); text(41, y, 71, colour); text(42, y, 83, colour)
    elif item == 2:
        text(34, y, 82, colour); text(35, y, 69, colour); text(36, y, 83, colour); text(37, y, 69, colour); text(38, y, 84, colour)
        text(40, y, 68, colour); text(41, y, 65, colour); text(42, y, 84, colour); text(43, y, 65, colour)
    elif item == 3:
        text(34, y, 83, colour); text(35, y, 84, colour); text(36, y, 65, colour); text(37, y, 84, colour); text(38, y, 73, colour)
        text(39, y, 83, colour); text(40, y, 84, colour); text(41, y, 73, colour); text(42, y, 67, colour); text(43, y, 83, colour)
    elif item == 4:
        text(33, y, 65, colour); text(34, y, 67, colour); text(35, y, 72, colour); text(36, y, 73, colour); text(37, y, 69, colour); text(38, y, 86, colour); text(39, y, 69, colour); text(40, y, 77, colour); text(41, y, 69, colour); text(42, y, 78, colour); text(43, y, 84, colour); text(44, y, 83, colour)
    elif item == 5:
        text(36, y, 71, colour); text(37, y, 76, colour); text(38, y, 73, colour); text(39, y, 84, colour); text(40, y, 67, colour); text(41, y, 72, colour)
    else:
        text(34, y, 69, colour); text(35, y, 88, colour); text(36, y, 84, colour); text(37, y, 69, colour); text(38, y, 78, colour); text(39, y, 83, colour); text(40, y, 73, colour); text(41, y, 79, colour); text(42, y, 78, colour)

def draw_menu() -> None:
    draw_menu_shell(0)
    first_item: i32 = menu_selection - 2 if menu_selection >= 3 else 0
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
    draw_achievement_popup()
def cycle_color_mode(direction: i32) -> None:
    global color_mode
    attempts: i32 = 0
    while attempts < 6:
        color_mode = (color_mode + direction + 6) % 6
        allowed: i32 = 1 if color_mode == 0 or color_mode == 2 else 0
        if color_mode == 1 and normal_achievement_count() >= 5: allowed = 1
        if color_mode == 3 and (achievements & (1 << 9)) != 0: allowed = 1
        if color_mode == 4 and (achievements & (1 << 11)) != 0: allowed = 1
        if color_mode == 5 and non_hidden_achievement_count() >= 14: allowed = 1
        if allowed == 1: return
        attempts = attempts + 1
    color_mode = 0
def draw_setting_value(value: i32, x: i32, y: i32) -> None:
    text(x, y, 48 + value // 10, 0x0F)
    text(x + 1, y, 48 + value % 10, 0x0F)

def draw_settings() -> None:
    draw_menu_shell(1)
    text(34, 4, 80, 0x0E); text(35, 4, 65, 0x0E); text(36, 4, 71, 0x0E); text(37, 4, 69, 0x0E)
    text(39, 4, 49 + settings_page, 0x0F); text(40, 4, 47, 0x07); text(41, 4, 51, 0x0F)
    cursor_y: i32 = 6 + settings_selection * 3 if settings_selection < 3 else 17
    text(20, cursor_y, 16, 0x0E)
    if settings_page == 0:
        # COLOR
        text(24, 6, 67, 0x0B); text(25, 6, 79, 0x0B); text(26, 6, 76, 0x0B); text(27, 6, 79, 0x0B); text(28, 6, 82, 0x0B)
        if color_mode == 0:
            text(42, 6, 78, 0x0F); text(43, 6, 79, 0x0F); text(44, 6, 82, 0x0F); text(45, 6, 77, 0x0F); text(46, 6, 65, 0x0F); text(47, 6, 76, 0x0F)
        elif color_mode == 1:
            text(39, 6, 71, 0x0F); text(40, 6, 82, 0x0F); text(41, 6, 65, 0x0F); text(42, 6, 89, 0x0F); text(43, 6, 83, 0x0F); text(44, 6, 67, 0x0F); text(45, 6, 65, 0x0F); text(46, 6, 76, 0x0F); text(47, 6, 69, 0x0F)
        elif color_mode == 2:
            text(40, 6, 73, 0x0F); text(41, 6, 78, 0x0F); text(42, 6, 86, 0x0F); text(43, 6, 69, 0x0F); text(44, 6, 82, 0x0F); text(45, 6, 84, 0x0F)
        elif color_mode == 3:
            text(40, 6, 75, 0x0F); text(41, 6, 79, 0x0F); text(42, 6, 78, 0x0F); text(43, 6, 65, 0x0F); text(44, 6, 77, 0x0F); text(45, 6, 73, 0x0F)
        elif color_mode == 4:
            text(43, 6, 48, 0x0F); text(44, 6, 49, 0x0F)
        else:
            text(40, 6, 71, 0x0F); text(41, 6, 79, 0x0F); text(42, 6, 76, 0x0F); text(43, 6, 68, 0x0F); text(44, 6, 69, 0x0F); text(45, 6, 78, 0x0F)
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
    elif settings_page == 1:
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
    else:
        # Achievement reward settings page.
        text(24, 6, 77, 0x0B); text(25, 6, 85, 0x0B); text(26, 6, 83, 0x0B); text(27, 6, 73, 0x0B); text(28, 6, 67, 0x0B)
        if music_mode == 0:
            text(37, 6, 75, 0x0F); text(38, 6, 79, 0x0F); text(39, 6, 82, 0x0F); text(40, 6, 79, 0x0F); text(41, 6, 66, 0x0F); text(42, 6, 69, 0x0F); text(43, 6, 73, 0x0F); text(44, 6, 78, 0x0F); text(45, 6, 73, 0x0F); text(46, 6, 75, 0x0F); text(47, 6, 73, 0x0F)
        elif music_mode == 1:
            text(39, 6, 75, 0x0F); text(40, 6, 65, 0x0F); text(41, 6, 76, 0x0F); text(42, 6, 73, 0x0F); text(43, 6, 78, 0x0F); text(44, 6, 75, 0x0F); text(45, 6, 65, 0x0F)
        else:
            music_name_x: i32 = 48 - music_name_length
            music_name_index: i32 = 0
            while music_name_index < music_name_length:
                text(music_name_x + music_name_index, 6, any_name_get(music_name_index), 0x0E)
                music_name_index = music_name_index + 1
        text(24, 9, 67, 0x0B); text(25, 9, 76, 0x0B); text(26, 9, 79, 0x0B); text(27, 9, 67, 0x0B); text(28, 9, 75, 0x0B)
        if (achievements & (1 << 12)) != 0:
            if clock_enabled == 1:
                text(44, 9, 79, 0x0F); text(45, 9, 78, 0x0F)
            else:
                text(43, 9, 79, 0x08); text(44, 9, 70, 0x08); text(45, 9, 70, 0x08)
        else:
            text(41, 9, 76, 0x08); text(42, 9, 79, 0x08); text(43, 9, 67, 0x08); text(44, 9, 75, 0x08); text(45, 9, 69, 0x08); text(46, 9, 68, 0x08)
        text(24, 12, 71, 0x0B); text(25, 12, 72, 0x0B); text(26, 12, 79, 0x0B); text(27, 12, 83, 0x0B); text(28, 12, 84, 0x0B)
        if ghost_enabled == 1:
            text(44, 12, 79, 0x0F); text(45, 12, 78, 0x0F)
        else:
            text(43, 12, 79, 0x08); text(44, 12, 70, 0x08); text(45, 12, 70, 0x08)
        text(34, 17, 83, 0x0A); text(35, 17, 65, 0x0A); text(36, 17, 86, 0x0A); text(37, 17, 69, 0x0A); text(39, 17, 66, 0x0A); text(40, 17, 65, 0x0A); text(41, 17, 67, 0x0A); text(42, 17, 75, 0x0A)
    footer_x: i32 = 30
    while footer_x < 50:
        ui_put_cell(footer_x, 17, 32, 0x10)
        footer_x = footer_x + 1
    has_reward_page: i32 = 1
    if settings_page == 0 or (settings_page == 1 and has_reward_page == 1):
        text(34, 17, 78, 0x0A); text(35, 17, 69, 0x0A); text(36, 17, 88, 0x0A); text(37, 17, 84, 0x0A)
        text(39, 17, 80, 0x0A); text(40, 17, 65, 0x0A); text(41, 17, 71, 0x0A); text(42, 17, 69, 0x0A)
    else:
        text(34, 17, 83, 0x0A); text(35, 17, 65, 0x0A); text(36, 17, 86, 0x0A); text(37, 17, 69, 0x0A)
        text(39, 17, 66, 0x0A); text(40, 17, 65, 0x0A); text(41, 17, 67, 0x0A); text(42, 17, 75, 0x0A)
    text(25, 21, 85, 0x07); text(26, 21, 80, 0x07); text(28, 21, 68, 0x07); text(29, 21, 79, 0x07); text(30, 21, 87, 0x07)
    text(33, 21, 76, 0x07); text(34, 21, 69, 0x07); text(35, 21, 70, 0x07); text(36, 21, 84, 0x07); text(38, 21, 82, 0x07); text(39, 21, 73, 0x07); text(40, 21, 71, 0x07); text(41, 21, 72, 0x07); text(42, 21, 84, 0x07)
def scancode_ascii(key: i32) -> i32:
    # US PC set-1 layout. Shift state is maintained by keyboard_scancode().
    letter: i32 = 0
    if key == 0x1E: letter = 65
    elif key == 0x30: letter = 66
    elif key == 0x2E: letter = 67
    elif key == 0x20: letter = 68
    elif key == 0x12: letter = 69
    elif key == 0x21: letter = 70
    elif key == 0x22: letter = 71
    elif key == 0x23: letter = 72
    elif key == 0x17: letter = 73
    elif key == 0x24: letter = 74
    elif key == 0x25: letter = 75
    elif key == 0x26: letter = 76
    elif key == 0x32: letter = 77
    elif key == 0x31: letter = 78
    elif key == 0x18: letter = 79
    elif key == 0x19: letter = 80
    elif key == 0x10: letter = 81
    elif key == 0x13: letter = 82
    elif key == 0x1F: letter = 83
    elif key == 0x14: letter = 84
    elif key == 0x16: letter = 85
    elif key == 0x2F: letter = 86
    elif key == 0x11: letter = 87
    elif key == 0x2D: letter = 88
    elif key == 0x15: letter = 89
    elif key == 0x2C: letter = 90
    if letter != 0:
        if keyboard_shifted == 0: return letter + 32
        return letter
    if key >= 0x02 and key <= 0x0A:
        if keyboard_shifted == 1:
            shifted_digits: i32 = 33
            if key == 0x03: shifted_digits = 64
            elif key == 0x04: shifted_digits = 35
            elif key == 0x05: shifted_digits = 36
            elif key == 0x06: shifted_digits = 37
            elif key == 0x07: shifted_digits = 94
            elif key == 0x08: shifted_digits = 38
            elif key == 0x09: shifted_digits = 42
            elif key == 0x0A: shifted_digits = 40
            return shifted_digits
        return 48 + key - 1
    if key == 0x0B: return 41 if keyboard_shifted == 1 else 48
    if key == 0x0C: return 95 if keyboard_shifted == 1 else 45
    if key == 0x0D: return 43 if keyboard_shifted == 1 else 61
    if key == 0x1A: return 123 if keyboard_shifted == 1 else 91
    if key == 0x1B: return 125 if keyboard_shifted == 1 else 93
    if key == 0x27: return 58 if keyboard_shifted == 1 else 59
    if key == 0x28: return 34 if keyboard_shifted == 1 else 39
    if key == 0x29: return 126 if keyboard_shifted == 1 else 96
    if key == 0x2B: return 124 if keyboard_shifted == 1 else 92
    if key == 0x33: return 60 if keyboard_shifted == 1 else 44
    if key == 0x34: return 62 if keyboard_shifted == 1 else 46
    if key == 0x35: return 63 if keyboard_shifted == 1 else 47
    if key == 0x39: return 32
    return 0

def draw_music_editor() -> None:
    clear_screen(0x10)
    name_index: i32 = 0
    while name_index < music_name_length:
        text(28 + name_index, 2, any_name_get(name_index), 0x0E)
        name_index = name_index + 1
    if music_name_editing == 1:
        text(28 + music_name_length, 2, 95, 0x0E)
    text(34, 2, 77, 0x0B); text(35, 2, 85, 0x0B); text(36, 2, 83, 0x0B); text(37, 2, 73, 0x0B); text(38, 2, 67, 0x0B)
    text(40, 2, 69, 0x0B); text(41, 2, 68, 0x0B); text(42, 2, 73, 0x0B); text(43, 2, 84, 0x0B); text(44, 2, 79, 0x0B); text(45, 2, 82, 0x0B)
    staff_y: i32 = 8
    while staff_y <= 16:
        staff_x: i32 = 7
        while staff_x < 73:
            ui_put_cell(staff_x, staff_y, 196, 0x17)
            staff_x = staff_x + 1
        staff_y = staff_y + 2
    note_index: i32 = 0
    while note_index < 32:
        packed_note: i32 = any_note_get(note_index)
        pitch: i32 = divisor_pitch(packed_note & 0xFFFF)
        note_y: i32 = 17 - pitch
        note_x: i32 = 8 + note_index * 2
        note_colour: i32 = 0x0E if note_index == music_editor_note else 0x0F
        note_duration: i32 = (packed_note >> 16) & 0xFFFF
        if (note_duration & 0x8000) == 0: ui_put_cell(note_x, note_y, 14, note_colour)
        if note_index == music_editor_note: ui_put_cell(note_x, 19, 30, 0x0E)
        note_index = note_index + 1
    text(8, 21, 65, 0x0B); text(9, 21, 82, 0x0B); text(10, 21, 82, 0x0B); text(11, 21, 79, 0x0B); text(12, 21, 87, 0x0B); text(13, 21, 83, 0x0B)
    text(15, 21, 77, 0x07); text(16, 21, 79, 0x07); text(17, 21, 86, 0x07); text(18, 21, 69, 0x07)
    text(21, 21, 69, 0x0A); text(22, 21, 78, 0x0A); text(23, 21, 84, 0x0A); text(24, 21, 69, 0x0A); text(25, 21, 82, 0x0A); text(27, 21, 83, 0x0A); text(28, 21, 65, 0x0A); text(29, 21, 86, 0x0A); text(30, 21, 69, 0x0A)
    text(33, 21, 69, 0x0C); text(34, 21, 83, 0x0C); text(35, 21, 67, 0x0C); text(37, 21, 67, 0x07); text(38, 21, 65, 0x07); text(39, 21, 78, 0x07); text(40, 21, 67, 0x07); text(41, 21, 69, 0x07); text(42, 21, 76, 0x07)
    text(45, 21, 82, 0x0E); text(47, 21, 82, 0x07); text(48, 21, 69, 0x07); text(49, 21, 83, 0x07); text(50, 21, 69, 0x07); text(51, 21, 84, 0x07)
    text(54, 21, 83, 0x0E); text(56, 21, 76, 0x07); text(57, 21, 73, 0x07); text(58, 21, 83, 0x07); text(59, 21, 84, 0x07); text(60, 21, 69, 0x07); text(61, 21, 78, 0x07)
    text(64, 21, 78, 0x0E); text(66, 21, 78, 0x07); text(67, 21, 65, 0x07); text(68, 21, 77, 0x07); text(69, 21, 69, 0x07)
    text(8, 23, 49, 0x0E); text(10, 23, 76, 0x07); text(11, 23, 79, 0x07); text(12, 23, 78, 0x07); text(13, 23, 71, 0x07)
    text(17, 23, 50, 0x0E); text(19, 23, 77, 0x07); text(20, 23, 73, 0x07); text(21, 23, 68, 0x07)
    text(25, 23, 51, 0x0E); text(27, 23, 83, 0x07); text(28, 23, 72, 0x07); text(29, 23, 79, 0x07); text(30, 23, 82, 0x07); text(31, 23, 84, 0x07)
    text(35, 23, 52, 0x0E); text(37, 23, 82, 0x07); text(38, 23, 69, 0x07); text(39, 23, 83, 0x07); text(40, 23, 84, 0x07)
    selected_duration: i32 = (any_note_get(music_editor_note) >> 16) & 0xFFFF
    selected_kind: i32 = 49
    if (selected_duration & 0x8000) != 0: selected_kind = 52
    elif selected_duration <= 20: selected_kind = 51
    elif selected_duration <= 40: selected_kind = 50
    text(68, 23, 68, 0x07); text(69, 23, 85, 0x07); text(70, 23, 82, 0x07); text(71, 23, 58, 0x07); text(72, 23, selected_kind, 0x0E)
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
