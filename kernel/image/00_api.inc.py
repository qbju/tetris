# Indexed-color image buffer for extensions: up to 65,536 pixels (typically 256x256).
IMAGE_BUFFER_SIZE: i32 = 65536
IMAGE_PERMISSION_PROCESS: i32 = 262144


def image_range_valid(offset: i32, length: i32) -> bool:
    return offset >= 0 and length >= 0 and offset <= IMAGE_BUFFER_SIZE and length <= IMAGE_BUFFER_SIZE - offset


def image_dimensions_valid(width: i32, height: i32) -> bool:
    return width > 0 and height > 0 and width <= 256 and height <= 256 and width * height <= IMAGE_BUFFER_SIZE


def extension_image_get(offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not image_range_valid(offset, 1): return -2
    return image_buffer_get(offset) & 255


def extension_image_set(offset: i32, colour: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not image_range_valid(offset, 1) or colour < 0 or colour > 255: return -2
    image_buffer_set(offset, colour)
    return 0


def extension_image_clear(length: i32, colour: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not image_range_valid(0, length) or colour < 0 or colour > 255: return -2
    index: i32 = 0
    while index < length:
        image_buffer_set(index, colour)
        index = index + 1
    return length


def extension_image_fill_rect(width: i32, height: i32, x: i32, y: i32, rect_width: i32, rect_height: i32, colour: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not image_dimensions_valid(width, height) or x < 0 or y < 0 or rect_width < 0 or rect_height < 0 or x + rect_width > width or y + rect_height > height or colour < 0 or colour > 255: return -2
    row: i32 = 0
    while row < rect_height:
        column: i32 = 0
        while column < rect_width:
            image_buffer_set((y + row) * width + x + column, colour)
            column = column + 1
        row = row + 1
    return rect_width * rect_height


def extension_image_flip_horizontal(width: i32, height: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not image_dimensions_valid(width, height): return -2
    row: i32 = 0
    while row < height:
        column: i32 = 0
        while column < width // 2:
            left: i32 = row * width + column
            right: i32 = row * width + width - 1 - column
            value: i32 = image_buffer_get(left)
            image_buffer_set(left, image_buffer_get(right))
            image_buffer_set(right, value)
            column = column + 1
        row = row + 1
    return width * height


def extension_image_flip_vertical(width: i32, height: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0: return -1
    if not image_dimensions_valid(width, height): return -2
    row: i32 = 0
    while row < height // 2:
        column: i32 = 0
        while column < width:
            top: i32 = row * width + column
            bottom: i32 = (height - 1 - row) * width + column
            value: i32 = image_buffer_get(top)
            image_buffer_set(top, image_buffer_get(bottom))
            image_buffer_set(bottom, value)
            column = column + 1
        row = row + 1
    return width * height


def extension_image_blit_scaled(width: i32, height: i32, destination_x: i32, destination_y: i32, destination_width: i32, destination_height: i32, transparent_colour: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & IMAGE_PERMISSION_PROCESS) == 0 or (extension_current_permissions & 1024) == 0: return -1
    if not image_dimensions_valid(width, height) or destination_x < 0 or destination_y < 0 or destination_width <= 0 or destination_height <= 0 or destination_x + destination_width > 640 or destination_y + destination_height > 480: return -2
    row: i32 = 0
    while row < destination_height:
        source_y: i32 = (row * height) // destination_height
        column: i32 = 0
        while column < destination_width:
            source_x: i32 = (column * width) // destination_width
            colour: i32 = image_buffer_get(source_y * width + source_x) & 255
            if colour != transparent_colour: ui_native_plot(destination_x + column, destination_y + row, colour)
            column = column + 1
        row = row + 1
    return destination_width * destination_height