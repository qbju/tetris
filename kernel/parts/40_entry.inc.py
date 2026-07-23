def draw_current_menu_page() -> None:
    if menu_page == 0:
        draw_menu()
    elif menu_page == 1:
        draw_settings()
    elif menu_page == 2:
        draw_reset_dialog()
    elif menu_page == 3:
        draw_statistics()
    elif menu_page == 4:
        draw_achievements()
    elif menu_page == 5:
        draw_build_info()
    elif menu_page == 6:
        draw_music_editor()
    elif menu_page == 7:
        draw_extensions()
    else:
        extension_draw(extension_active)
    draw_extension_notification()


def begin_ui_transition() -> None:
    global ui_transition_active
    if extension_transition_enabled() != 0:
        extension_transition_begin()
        ui_transition_active = 1
        ui_present_diff(0)
    else:
        ui_transition_active = 0
        ui_present_diff(320)


def update_ui_transition() -> None:
    global ui_transition_active
    if ui_transition_active == 0: return
    reveal: i32 = extension_transition_step()
    if reveal < 0: reveal = 0
    if reveal > 320: reveal = 320
    ui_present_diff(reveal)
    if reveal >= 320: ui_transition_active = 0

def kernel_main() -> None:
    global piece_x, piece_y, rotation, ticks, key_cooldown, started, last_key, menu_drawn, grounded, game_initialized, game_over_drawn, debug_visible, menu_page, menu_selection, settings_selection, settings_page, reset_choice, color_mode, gravity_periods, control_mode, keyboard_layout, bgm_volume, se_volume, debug_enabled, clock_enabled, ghost_enabled, debug_visible, fps_value, fps_frames, fps_deadline, total_play_periods, total_lines, total_pieces, stats_last_period, achievement_selection, achievement_detail_open, game_mode, sprint_lines, sprint_start_period, sprint_elapsed_periods, session_hold_used, session_tspins, last_action_rotation, survivor_start_period, score, music_mode, music_editor_note, music_name_editing, music_name_length, extension_selection, extension_active, ui_transition_active, extension_notification_source, extension_notification_dirty, extension_redraw_requested
    vga_set_mode13()
    cell: i32 = 0
    while cell < 240:
        board_set(cell, 0)
        cell = cell + 1
    pit_init()
    boot_screen()
    vga_set_palette(color_mode)
    startup_extension: i32 = fs_autostart_identifier()
    if boot_safe_mode == 0 and startup_extension >= 0 and startup_extension < extension_count() and extension_background_capable(startup_extension) != 0:
        extension_enter(startup_extension)
        extension_background_start(startup_extension)
        menu_page = 0
        menu_drawn = 0
    redraw: i32 = 0
    while True:
        redraw = 0
        pit_update_clock()
        sound_update()
        extension_background_update_all()
        if started == 0 and menu_page == 8:
            extension_update(extension_active)
            if extension_redraw_requested == 1:
                extension_redraw_requested = 0
                menu_drawn = 0
        key: i32 = keyboard_scancode()
        if started == 1 and system_periods > stats_last_period:
            total_play_periods = total_play_periods + system_periods - stats_last_period
            if total_play_periods >= 360000: unlock_achievement(6)
            stats_last_period = system_periods
        if started == 1 and game_over == 0 and gravity_periods <= 30 and system_periods - survivor_start_period >= 30000:
            unlock_achievement(21)
        if key != 0:
            last_key = key
        if debug_enabled == 1 and menu_page != 8 and (key == 0x2A or key == 0x36):
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
                ui_set_render_target(1)
                draw_current_menu_page()
                ui_set_render_target(0)
                if menu_page == 8:
                    ui_transition_active = 0
                    ui_present_diff(320)
                    extension_native_overlay(extension_active)
                else:
                    begin_ui_transition()
                menu_drawn = 1
                debug_reset()
            elif ui_transition_active == 1:
                update_ui_transition()
            elif debug_visible == 1 and menu_page == 0 and key != 0:
                put_hex8(last_key, 48, 19)
            if menu_page == 0:
                menu_count: i32 = 7 if extension_count() > 0 else (6 if (achievements & (1 << 13)) != 0 else 5)
                update_konami(key)
                if key == 0x48:
                    menu_selection = (menu_selection + menu_count - 1) % menu_count
                    sound_tone(1808, 1)
                    menu_drawn = 0
                elif key == 0x50:
                    menu_selection = (menu_selection + 1) % menu_count
                    sound_tone(1591, 1)
                    menu_drawn = 0
                elif (key == 0x4B or key == 0x4D) and menu_selection == 0:
                    game_mode = (game_mode + (2 if key == 0x4B else 1)) % 3
                    game_initialized = 0
                    sound_tone(1591, 1)
                    menu_drawn = 0
                elif key == 0x1C:
                    sound_tone(1193, 2)
                    if menu_selection == 0:
                        started = 1
                        clear_screen(0x10)
                        if game_initialized == 0:
                            reset_game()
                        # Menu time must not count toward the first gravity step.
                        pit_reset_elapsed()
                        arm_move_cooldown(15)
                        debug_reset()
                        music_start()
                        stats_last_period = system_periods
                        survivor_start_period = system_periods
                        extension_emit_event(4, game_mode)
                        draw()
                    elif menu_selection == 1:
                        menu_page = 1
                        settings_selection = 0
                        settings_page = 0
                        menu_drawn = 0
                    elif menu_selection == 2:
                        menu_page = 2
                        reset_choice = 1
                        menu_drawn = 0
                    elif menu_selection == 3:
                        menu_page = 3
                        menu_drawn = 0
                    elif menu_selection == 4:
                        menu_page = 4
                        achievement_page = 0
                        menu_drawn = 0
                    elif menu_selection == 5:
                        menu_page = 5
                        menu_drawn = 0
                    else:
                        extension_selection = 0
                        menu_page = 7
                        menu_drawn = 0
            elif menu_page == 1:
                if key == 0x48:
                    settings_selection = (3 if settings_selection == 0 else 0) if settings_page == 3 else (settings_selection + 3) % 4
                    menu_drawn = 0
                elif key == 0x50:
                    settings_selection = (3 if settings_selection == 0 else 0) if settings_page == 3 else (settings_selection + 1) % 4
                    menu_drawn = 0
                elif key == 0x4B or key == 0x4D:
                    direction: i32 = -1 if key == 0x4B else 1
                    if settings_page == 0:
                        if settings_selection == 0:
                            cycle_color_mode(direction)
                            vga_set_palette(color_mode)
                        elif settings_selection == 1:
                            gravity_periods = gravity_periods + direction * 10
                            minimum_gravity: i32 = 10 if normal_achievement_count() >= 9 else 40
                            if gravity_periods < minimum_gravity: gravity_periods = minimum_gravity
                            if gravity_periods > 100: gravity_periods = 100
                        elif settings_selection == 2:
                            control_mode = 1 - control_mode
                    elif settings_page == 1:
                        if settings_selection == 0:
                            bgm_volume = bgm_volume + direction
                            if bgm_volume < 0: bgm_volume = 0
                            if bgm_volume > 10: bgm_volume = 10
                        elif settings_selection == 1:
                            se_volume = se_volume + direction
                            if se_volume < 0: se_volume = 0
                            if se_volume > 10: se_volume = 10
                        elif settings_selection == 2:
                            debug_enabled = 1 - debug_enabled
                            if debug_enabled == 0: debug_visible = 0
                    elif settings_page == 2:
                        if settings_selection == 0:
                            candidate_music: i32 = music_mode
                            music_attempt: i32 = 0
                            while music_attempt < 3:
                                candidate_music = (candidate_music + direction + 3) % 3
                                if candidate_music == 0 or (candidate_music == 1 and (achievements & (1 << 10)) != 0) or (candidate_music == 2 and non_hidden_achievement_count() >= 19):
                                    music_mode = candidate_music
                                    music_attempt = 3
                                else:
                                    music_attempt = music_attempt + 1
                        elif settings_selection == 1 and (achievements & (1 << 12)) != 0:
                            clock_enabled = 1 - clock_enabled
                        elif settings_selection == 2:
                            ghost_enabled = 1 - ghost_enabled
                    else:
                        if settings_selection == 0: keyboard_layout = (keyboard_layout + direction + keyboard_layout_count()) % keyboard_layout_count()
                    menu_drawn = 0
                elif key == 0x1C:
                    if settings_page == 2 and settings_selection == 0 and music_mode == 2 and non_hidden_achievement_count() >= 19:
                        music_editor_note = 0
                        music_name_editing = 0
                        menu_page = 6
                        menu_drawn = 0
                    elif settings_page == 3 and settings_selection == 0:
                        settings_selection = 3
                        menu_drawn = 0
                    elif settings_selection < 3:
                        settings_selection = settings_selection + 1
                        menu_drawn = 0
                    else:
                        has_reward_page: i32 = 1
                        if settings_page < 3:
                            settings_page = settings_page + 1
                            settings_selection = 0
                            menu_drawn = 0
                        else:
                            fs_save_settings()
                            settings_page = 0
                            menu_page = 0
                            menu_drawn = 0
                elif key == 0x01:
                    if settings_page > 0:
                        settings_page = settings_page - 1
                        settings_selection = 0
                        menu_drawn = 0
                    else:
                        fs_save_settings()
                        menu_page = 0
                        menu_drawn = 0
            elif menu_page == 2:
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
            elif menu_page == 7:
                extension_total: i32 = extension_count()
                if key == 0x48 and extension_total > 0:
                    extension_selection = (extension_selection + extension_total - 1) % extension_total
                    menu_drawn = 0
                elif key == 0x50 and extension_total > 0:
                    extension_selection = (extension_selection + 1) % extension_total
                    menu_drawn = 0
                elif key == 0x1C and extension_total > 0:
                    if keyboard_shifted == 1:
                        configured_extension: i32 = fs_autostart_identifier()
                        if configured_extension == extension_selection:
                            fs_set_autostart(extension_selection, 0)
                            sound_tone(1808, 1)
                        elif extension_background_capable(extension_selection) != 0:
                            fs_set_autostart(extension_selection, 1)
                            sound_tone(1193, 2)
                        else:
                            sound_tone(904, 3)
                    else:
                        extension_active = extension_selection
                        extension_enter(extension_active)
                        menu_page = 8
                    menu_drawn = 0
                elif key == 0x01:
                    menu_page = 0
                    menu_selection = 6
                    menu_drawn = 0
            elif menu_page == 8:
                extension_result: i32 = extension_key(extension_active, key)
                if extension_result == 3:
                    menu_drawn = 0
                elif key == 0x01 or extension_result != 0:
                    extension_exit(extension_active)
                    if extension_result == 2:
                        menu_page = 0
                        menu_selection = 0
                    else:
                        vga_set_palette(color_mode)
                        menu_page = 7
                    menu_drawn = 0
                elif key != 0:
                    menu_drawn = 0
            elif menu_page == 6:
                if music_name_editing == 1:
                    if key == 0x1C:
                        if music_name_length > 0: music_name_editing = 0
                    elif key == 0x01:
                        music_name_editing = 0
                    elif key == 0x0E and music_name_length > 0:
                        music_name_length = music_name_length - 1
                        any_name_set(music_name_length, 0)
                    else:
                        name_character: i32 = scancode_ascii(key)
                        if name_character != 0 and music_name_length < 8:
                            any_name_set(music_name_length, name_character)
                            music_name_length = music_name_length + 1
                    menu_drawn = 0
                elif key == 0x4B:
                    music_editor_note = (music_editor_note + 31) % 32
                    menu_drawn = 0
                elif key == 0x4D:
                    music_editor_note = (music_editor_note + 1) % 32
                    menu_drawn = 0
                elif key == 0x48 or key == 0x50:
                    editor_note: i32 = any_note_get(music_editor_note)
                    editor_pitch: i32 = divisor_pitch(editor_note & 0xFFFF)
                    if key == 0x48 and editor_pitch < 11: editor_pitch = editor_pitch + 1
                    if key == 0x50 and editor_pitch > -2: editor_pitch = editor_pitch - 1
                    any_note_set(music_editor_note, pitch_divisor(editor_pitch) | (editor_note & 0xFFFF0000))
                    menu_drawn = 0
                elif key >= 0x02 and key <= 0x05:
                    duration_note: i32 = any_note_get(music_editor_note)
                    duration_value: i32 = 80
                    if key == 0x03: duration_value = 40
                    elif key == 0x04: duration_value = 20
                    elif key == 0x05: duration_value = 0x8000 | 40
                    any_note_set(music_editor_note, (duration_note & 0xFFFF) | (duration_value << 16))
                    menu_drawn = 0
                elif key == 0x31:
                    music_name_editing = 1
                    menu_drawn = 0
                elif key == 0x13:
                    any_music_reset()
                    menu_drawn = 0
                elif key == 0x1F:
                    music_start()
                elif key == 0x1C:
                    music_stop()
                    fs_save_any_music()
                    fs_save_settings()
                    menu_page = 1
                    settings_page = 2
                    settings_selection = 0
                    menu_drawn = 0
                elif key == 0x01:
                    music_stop()
                    fs_load_any_music()
                    menu_page = 1
                    settings_page = 2
                    settings_selection = 0
                    menu_drawn = 0
            elif menu_page == 3 or menu_page == 5:
                if key == 0x1C or key == 0x01:
                    menu_page = 0
                    menu_drawn = 0
            else:
                if achievement_detail_open == 1:
                    if key == 0x1C or key == 0x01:
                        achievement_detail_open = 0
                        menu_drawn = 0
                elif key == 0x48:
                    achievement_selection = (achievement_selection + 23) % 24
                    achievement_page = achievement_selection // 7
                    menu_drawn = 0
                elif key == 0x50:
                    achievement_selection = (achievement_selection + 1) % 24
                    achievement_page = achievement_selection // 7
                    menu_drawn = 0
                elif key == 0x4B or key == 0x4D:
                    if key == 0x4B: achievement_page = (achievement_page + 3) % 4
                    else: achievement_page = (achievement_page + 1) % 4
                    achievement_selection = achievement_page * 7
                    menu_drawn = 0
                elif key == 0x1C:
                    achievement_detail_open = 1
                    menu_drawn = 0
                elif key == 0x01:
                    menu_page = 0
                    menu_drawn = 0
        elif game_over == 0:
            left_code: i32 = 0x4B if control_mode == 0 else 0x1E
            right_code: i32 = 0x4D if control_mode == 0 else 0x20
            down_code: i32 = 0x50 if control_mode == 0 else 0x1F
            rotate_code: i32 = 0x48 if control_mode == 0 else 0x11
            if key == 0x01:
                music_stop()
                finish_session()
                started = 0
                menu_page = 0
                menu_drawn = 0
                arm_move_cooldown(15)
            if move_ready() and key == left_code and fits(piece_x - 1, piece_y, rotation):
                piece_x = piece_x - 1
                last_action_rotation = 0
                arm_move_cooldown(10)
                redraw = 1
            if move_ready() and key == right_code and fits(piece_x + 1, piece_y, rotation):
                piece_x = piece_x + 1
                last_action_rotation = 0
                arm_move_cooldown(10)
                redraw = 1
            if move_ready() and key == down_code and fits(piece_x, piece_y + 1, rotation):
                piece_y = piece_y + 1
                last_action_rotation = 0
                arm_move_cooldown(5)
                redraw = 1
                if not fits(piece_x, piece_y + 1, rotation):
                    grounded = 1
                    pit_reset_elapsed()
            if move_ready() and key == rotate_code and try_rotate_clockwise() == 1:
                last_action_rotation = 1
                sound_tone(1356, 1)
                arm_move_cooldown(15)
                redraw = 1
            if move_ready() and key == 0x2E:
                hold_piece()
                sound_tone(1591, 2)
                arm_move_cooldown(15)
                redraw = 1
            timer_ready: i32 = pit_poll_elapsed(20 if grounded == 1 else gravity_periods)
            if timer_ready != 0:
                if grounded == 1 and not fits(piece_x, piece_y + 1, rotation):
                    completed_t_spin: i32 = 1 if is_t_spin() else 0
                    merge_piece()
                    extension_emit_event(5, kind)
                    if completed_t_spin == 1:
                        session_tspins = session_tspins + 1
                        score = score + 400
                        unlock_achievement(22)
                        if session_tspins >= 5: unlock_achievement(23)
                    flash_completed_lines()
                    cleared_lines: i32 = clear_lines()
                    if cleared_lines > 0: extension_emit_event(1, cleared_lines)
                    update_combo(cleared_lines)
                    if cleared_lines > 0 and board_is_empty(): unlock_achievement(19)
                    if ghost_enabled == 0 and score > 1000: unlock_achievement(20)
                    sprint_lines = session_lines
                    if cleared_lines > 0:
                        sound_line_clear()
                    else:
                        sound_tone(2386, 2)
                    mode_finished: i32 = 1 if (game_mode == 1 and sprint_lines >= 150) or (game_mode == 2 and sprint_lines >= 40) else 0
                    if mode_finished == 1:
                        if game_mode == 1 and session_hold_used == 0: unlock_achievement(17)
                        if game_mode == 2 and session_hold_used == 0: unlock_achievement(18)
                        sprint_elapsed_periods = system_periods - sprint_start_period
                        game_over = 2
                    else:
                        spawn()
                    redraw = 1
                elif fits(piece_x, piece_y + 1, rotation):
                    grounded = 0
                    piece_y = piece_y + 1
                    last_action_rotation = 0
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
                music_stop()
                fs_save_high_score(score)
                finish_session()
                sound_game_over()
                if game_over == 2: draw_mode_complete()
                else: draw_game_over()
                game_over_drawn = 1
            if key == 0x1C:
                started = 0
                menu_page = 0
                menu_drawn = 0
                game_initialized = 0
                game_over_drawn = 0
                arm_move_cooldown(15)
                debug_reset()
        if extension_notification_dirty == 1:
            extension_notification_dirty = 0
            if started == 1 and game_over == 0: draw()
            else: menu_drawn = 0
        if extension_notification_source >= 0 and system_periods >= extension_notification_until:
            extension_notification_source = -1
            if started == 1 and game_over == 0: draw()
            else: menu_drawn = 0
        if achievement_popup >= 0 and system_periods >= achievement_popup_until:
            achievement_popup = -1
            if started == 1 and game_over == 0:
                draw()
            else:
                menu_drawn = 0
        if started == 0 and menu_page == 6:
            music_update()
        if started == 1 and game_over == 0:
            if system_periods >= fps_deadline:
                fps_value = fps_frames
                fps_frames = 0
                fps_deadline = system_periods + 100
            music_update()
        if debug_visible == 1 and started == 1:
            debug_status()


kernel_main()
