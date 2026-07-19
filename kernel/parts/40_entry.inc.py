def kernel_main() -> None:
    global piece_x, piece_y, rotation, ticks, key_cooldown, started, last_key, menu_drawn, grounded, game_initialized, game_over_drawn, debug_visible, menu_page, menu_selection, settings_selection, settings_page, reset_choice, color_mode, gravity_periods, control_mode, bgm_volume, se_volume, debug_enabled, debug_visible, fps_value, fps_frames, fps_deadline, total_play_periods, total_lines, total_pieces, stats_last_period
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
        pit_update_clock()
        sound_update()
        key: i32 = keyboard_scancode()
        if started == 1 and system_periods > stats_last_period:
            total_play_periods = total_play_periods + system_periods - stats_last_period
            stats_last_period = system_periods
        if key != 0:
            last_key = key
        if debug_enabled == 1 and (key == 0x2A or key == 0x36):
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
                elif menu_page == 2:
                    draw_reset_dialog()
                else:
                    draw_statistics()
                menu_drawn = 1
                debug_reset()
            elif debug_visible == 1 and menu_page == 0 and key != 0:
                put_hex8(last_key, 48, 19)

            if menu_page == 0:
                if key == 0x48:
                    menu_selection = (menu_selection + 3) % 4
                    sound_tone(1808, 1)
                    menu_drawn = 0
                elif key == 0x50:
                    menu_selection = (menu_selection + 1) % 4
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
                    else:
                        menu_page = 3
                        menu_drawn = 0
            elif menu_page == 1:
                if key == 0x48:
                    settings_selection = (settings_selection + 3) % 4
                    menu_drawn = 0
                elif key == 0x50:
                    settings_selection = (settings_selection + 1) % 4
                    menu_drawn = 0
                elif key == 0x4B or key == 0x4D:
                    direction: i32 = -1 if key == 0x4B else 1
                    if settings_page == 0:
                        if settings_selection == 0:
                            color_mode = (color_mode + direction + 3) % 3
                            vga_set_palette(color_mode)
                        elif settings_selection == 1:
                            gravity_periods = gravity_periods + direction * 10
                            if gravity_periods < 10: gravity_periods = 10
                            if gravity_periods > 100: gravity_periods = 100
                        elif settings_selection == 2:
                            control_mode = 1 - control_mode
                    else:
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
                    menu_drawn = 0
                elif key == 0x1C:
                    if settings_selection < 3:
                        settings_selection = settings_selection + 1
                        menu_drawn = 0
                    elif settings_page == 0:
                        settings_page = 1
                        settings_selection = 0
                        menu_drawn = 0
                    else:
                        fs_save_settings()
                        settings_page = 0
                        menu_page = 0
                        menu_drawn = 0
                elif key == 0x01:
                    if settings_page == 1:
                        settings_page = 0
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
            else:
                if key == 0x1C or key == 0x01:
                    menu_page = 0
                    menu_drawn = 0
        elif game_over == 0:
            left_code: i32 = 0x4B if control_mode == 0 else 0x1E
            right_code: i32 = 0x4D if control_mode == 0 else 0x20
            down_code: i32 = 0x50 if control_mode == 0 else 0x1F
            rotate_code: i32 = 0x48 if control_mode == 0 else 0x11
            if key == 0x01:
                music_stop()
                fs_save_statistics()
                started = 0
                menu_page = 0
                menu_drawn = 0
                arm_move_cooldown(15)
            if move_ready() and key == left_code and fits(piece_x - 1, piece_y, rotation):
                piece_x = piece_x - 1
                arm_move_cooldown(10)
                redraw = 1
            if move_ready() and key == right_code and fits(piece_x + 1, piece_y, rotation):
                piece_x = piece_x + 1
                arm_move_cooldown(10)
                redraw = 1
            if move_ready() and key == down_code and fits(piece_x, piece_y + 1, rotation):
                piece_y = piece_y + 1
                arm_move_cooldown(5)
                redraw = 1
                if not fits(piece_x, piece_y + 1, rotation):
                    grounded = 1
                    pit_reset_elapsed()
            if move_ready() and key == rotate_code and fits(piece_x, piece_y, (rotation + 1) % 4):
                rotation = (rotation + 1) % 4
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
                    merge_piece()
                    cleared_lines: i32 = clear_lines()
                    update_combo(cleared_lines)
                    if cleared_lines > 0:
                        sound_line_clear()
                    else:
                        sound_tone(2386, 2)
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
                music_stop()
                fs_save_high_score(score)
                fs_save_statistics()
                sound_game_over()
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
        if started == 1 and game_over == 0:
            if system_periods >= fps_deadline:
                fps_value = fps_frames
                fps_frames = 0
                fps_deadline = system_periods + 100
            music_update()
        if debug_visible == 1 and started == 1:
            debug_status()


kernel_main()
