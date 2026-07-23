# GIF87a/GIF89a first-frame decoder. Indexed output is written into image_buffer.
GIF_INPUT_SIZE: i32 = 1048576
gif_builtin_mode: i32 = 0

def gif_data_get(index: i32) -> i32:
    if gif_builtin_mode == 1: return builtin_gif_get(index)
    return gif_input_get(index)


def gif_input_valid(offset: i32, length: i32) -> bool:
    return offset >= 0 and length >= 0 and offset <= GIF_INPUT_SIZE and length <= GIF_INPUT_SIZE - offset


def extension_gif_input_get(offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not gif_input_valid(offset, 1): return -2
    return gif_input_get(offset) & 255


def extension_gif_input_set(offset: i32, value: i32) -> i32:
    global gif_builtin_mode
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not gif_input_valid(offset, 1) or value < 0 or value > 255: return -2
    gif_builtin_mode = 0
    gif_input_set(offset, value)
    return 0



def extension_gif_load_builtin() -> i32:
    global gif_builtin_mode
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    length: i32 = builtin_gif_size()
    if not gif_input_valid(0, length): return -2
    gif_builtin_mode = 1
    return length
def gif_u16(offset: i32) -> i32:
    return (gif_data_get(offset) & 255) | ((gif_data_get(offset + 1) & 255) << 8)


def gif_skip_subblocks(position: i32, input_length: i32) -> i32:
    cursor: i32 = position
    while cursor < input_length:
        count: i32 = gif_data_get(cursor) & 255
        cursor = cursor + 1
        if count == 0: return cursor
        if cursor + count > input_length: return -1
        cursor = cursor + count
    return -1


def gif_load_palette(position: i32, count: i32, input_length: i32) -> i32:
    if position + count * 3 > input_length: return -1
    index: i32 = 0
    while index < count:
        # VGA DAC stores 6-bit RGB; GIF table values are 8-bit RGB.
        ui_set_palette_entry(index, (gif_data_get(position + index * 3) & 255) >> 2, (gif_data_get(position + index * 3 + 1) & 255) >> 2, (gif_data_get(position + index * 3 + 2) & 255) >> 2)
        index = index + 1
    return position + count * 3


def extension_gif_restore_palette() -> i32:
    if extension_current_id < 0 or (extension_current_permissions & 1024) == 0: return -1
    vga_set_palette(color_mode)
    return 0


def extension_gif_decode_frame(input_length: i32, target_frame: i32) -> i32:
    # Supports first frame, global/local palette and GIF LZW. Interlaced GIFs are rejected for now.
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0 or (extension_current_permissions & 1024) == 0: return -1
    if not gif_input_valid(0, input_length) or input_length < 13: return -2
    if gif_data_get(0) != 71 or gif_data_get(1) != 73 or gif_data_get(2) != 70: return -3
    if (gif_data_get(3) != 56 or gif_data_get(4) != 55 or (gif_data_get(5) != 97 and gif_data_get(5) != 65)): return -3
    screen_width: i32 = gif_u16(6)
    screen_height: i32 = gif_u16(8)
    if not image_dimensions_valid(screen_width, screen_height): return -4
    packed: i32 = gif_data_get(10) & 255
    cursor: i32 = 13
    if (packed & 128) != 0:
        table_count: i32 = 1 << ((packed & 7) + 1)
        cursor = gif_load_palette(cursor, table_count, input_length)
        if cursor < 0: return -5
    transparent: i32 = -1
    frame_index: i32 = 0
    while cursor < input_length:
        marker: i32 = gif_data_get(cursor) & 255
        cursor = cursor + 1
        if marker == 59: return -6
        if marker == 33:
            if cursor >= input_length: return -5
            label: i32 = gif_data_get(cursor) & 255
            cursor = cursor + 1
            if label == 249:
                if cursor + 6 > input_length or gif_data_get(cursor) != 4: return -5
                control: i32 = gif_data_get(cursor + 1) & 255
                if (control & 1) != 0: transparent = gif_data_get(cursor + 4) & 255
                cursor = cursor + 6
            else:
                cursor = gif_skip_subblocks(cursor, input_length)
                if cursor < 0: return -5
        elif marker == 44:
            if cursor + 9 > input_length: return -5
            left: i32 = gif_u16(cursor)
            top: i32 = gif_u16(cursor + 2)
            width: i32 = gif_u16(cursor + 4)
            height: i32 = gif_u16(cursor + 6)
            image_packed: i32 = gif_data_get(cursor + 8) & 255
            cursor = cursor + 9
            if frame_index != target_frame:
                skip_cursor: i32 = cursor
                if (image_packed & 128) != 0:
                    skip_cursor = skip_cursor + 3 * (1 << ((image_packed & 7) + 1))
                if skip_cursor >= input_length: return -5
                cursor = gif_skip_subblocks(skip_cursor + 1, input_length)
                if cursor < 0: return -5
                frame_index = frame_index + 1
                continue
            if width <= 0 or height <= 0 or left + width > screen_width or top + height > screen_height: return -4
            if (image_packed & 64) != 0: return -7
            if (image_packed & 128) != 0:
                local_count: i32 = 1 << ((image_packed & 7) + 1)
                cursor = gif_load_palette(cursor, local_count, input_length)
                if cursor < 0: return -5
            if cursor >= input_length: return -5
            minimum_code_size: i32 = gif_data_get(cursor) & 255
            cursor = cursor + 1
            if minimum_code_size < 2 or minimum_code_size > 8: return -8
            clear_code: i32 = 1 << minimum_code_size
            end_code: i32 = clear_code + 1
            next_code: i32 = end_code + 1
            code_size: i32 = minimum_code_size + 1
            code_limit: i32 = 1 << code_size
            index: i32 = 0
            while index < clear_code:
                gif_prefix_set(index, 0)
                gif_suffix_set(index, index)
                index = index + 1
            data_remaining: i32 = 0
            bit_buffer: i32 = 0
            bit_count: i32 = 0
            old_code: i32 = -1
            first: i32 = 0
            pixel: i32 = 0
            done: i32 = 0
            while done == 0:
                while bit_count < code_size:
                    if data_remaining == 0:
                        if cursor >= input_length: return -5
                        data_remaining = gif_data_get(cursor) & 255
                        cursor = cursor + 1
                        if data_remaining == 0: return -5
                    if cursor >= input_length: return -5
                    bit_buffer = bit_buffer | ((gif_data_get(cursor) & 255) << bit_count)
                    bit_count = bit_count + 8
                    cursor = cursor + 1
                    data_remaining = data_remaining - 1
                code: i32 = bit_buffer & ((1 << code_size) - 1)
                bit_buffer = bit_buffer >> code_size
                bit_count = bit_count - code_size
                if code == clear_code:
                    next_code = end_code + 1
                    code_size = minimum_code_size + 1
                    code_limit = 1 << code_size
                    old_code = -1
                elif code == end_code:
                    done = 1
                elif code > 4095:
                    return -8
                elif old_code < 0:
                    if code >= clear_code: return -8
                    first = gif_suffix_get(code) & 255
                    if pixel >= width * height: return -8
                    if first != transparent: image_buffer_set((top + pixel // width) * screen_width + left + pixel % width, first)
                    pixel = pixel + 1
                    old_code = code
                else:
                    input_code: i32 = code
                    stack_count: i32 = 0
                    if code >= next_code:
                        gif_stack_set(stack_count, first)
                        stack_count = stack_count + 1
                        code = old_code
                    while code >= clear_code:
                        if code >= next_code or stack_count >= 4096: return -8
                        gif_stack_set(stack_count, gif_suffix_get(code) & 255)
                        stack_count = stack_count + 1
                        code = gif_prefix_get(code)
                    if code >= clear_code: return -8
                    first = gif_suffix_get(code) & 255
                    gif_stack_set(stack_count, first)
                    stack_count = stack_count + 1
                    while stack_count > 0:
                        stack_count = stack_count - 1
                        value: i32 = gif_stack_get(stack_count) & 255
                        if pixel >= width * height: return -8
                        if value != transparent: image_buffer_set((top + pixel // width) * screen_width + left + pixel % width, value)
                        pixel = pixel + 1
                    if next_code < 4096:
                        gif_prefix_set(next_code, old_code)
                        gif_suffix_set(next_code, first)
                        next_code = next_code + 1
                        if next_code >= code_limit and code_size < 12:
                            code_size = code_size + 1
                            code_limit = code_limit << 1
                    old_code = input_code
            if pixel != width * height: return -8
            return screen_width * screen_height
        else:
            return -3
    return -5
def extension_gif_decode(input_length: i32) -> i32:
    return extension_gif_decode_frame(input_length, 0)
