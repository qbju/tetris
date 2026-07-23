def crypt_base64_character(value: i32) -> i32:
    if value < 26: return 65 + value
    if value < 52: return 97 + value - 26
    if value < 62: return 48 + value - 52
    if value == 62: return 43
    return 47


def crypt_base64_value(character: i32) -> i32:
    if character >= 65 and character <= 90: return character - 65
    if character >= 97 and character <= 122: return character - 97 + 26
    if character >= 48 and character <= 57: return character - 48 + 52
    if character == 43: return 62
    if character == 47: return 63
    return -1


def crypt_base64_encode(input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    output_length: i32 = ((input_length + 2) // 3) * 4
    if not crypt_range_valid(input_offset, input_length) or not crypt_range_valid(output_offset, output_length): return -2
    source: i32 = 0
    target: i32 = 0
    while source < input_length:
        remaining: i32 = input_length - source
        first: i32 = crypt_buffer_get(input_offset + source) & 255
        second: i32 = crypt_buffer_get(input_offset + source + 1) & 255 if remaining > 1 else 0
        third: i32 = crypt_buffer_get(input_offset + source + 2) & 255 if remaining > 2 else 0
        crypt_buffer_set(output_offset + target, crypt_base64_character(first >> 2))
        crypt_buffer_set(output_offset + target + 1, crypt_base64_character(((first & 3) << 4) | (second >> 4)))
        crypt_buffer_set(output_offset + target + 2, crypt_base64_character(((second & 15) << 2) | (third >> 6)) if remaining > 1 else 61)
        crypt_buffer_set(output_offset + target + 3, crypt_base64_character(third & 63) if remaining > 2 else 61)
        source = source + 3
        target = target + 4
    return output_length


def crypt_base64_decode(input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if input_length % 4 != 0 or not crypt_range_valid(input_offset, input_length): return -2
    padding: i32 = 0
    if input_length > 0 and crypt_buffer_get(input_offset + input_length - 1) == 61: padding = padding + 1
    if input_length > 1 and crypt_buffer_get(input_offset + input_length - 2) == 61: padding = padding + 1
    output_length: i32 = (input_length // 4) * 3 - padding
    if not crypt_range_valid(output_offset, output_length): return -2
    source: i32 = 0
    target: i32 = 0
    while source < input_length:
        a: i32 = crypt_base64_value(crypt_buffer_get(input_offset + source))
        b: i32 = crypt_base64_value(crypt_buffer_get(input_offset + source + 1))
        cchar: i32 = crypt_buffer_get(input_offset + source + 2)
        dchar: i32 = crypt_buffer_get(input_offset + source + 3)
        c: i32 = 0 if cchar == 61 else crypt_base64_value(cchar)
        d: i32 = 0 if dchar == 61 else crypt_base64_value(dchar)
        if a < 0 or b < 0 or c < 0 or d < 0: return -3
        if cchar == 61 and (source + 4 != input_length or dchar != 61): return -3
        if dchar == 61 and source + 4 != input_length: return -3
        if target < output_length: crypt_buffer_set(output_offset + target, (a << 2) | (b >> 4))
        if target + 1 < output_length: crypt_buffer_set(output_offset + target + 1, ((b & 15) << 4) | (c >> 2))
        if target + 2 < output_length: crypt_buffer_set(output_offset + target + 2, ((c & 3) << 6) | d)
        source = source + 4
        target = target + 3
    return output_length