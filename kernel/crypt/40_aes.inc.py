# FIPS 197 AES-128 block cipher and CTR mode, implemented in pure LPython.
AES_KEY_SCRATCH: i32 = 4608
AES_STATE_SCRATCH: i32 = 4800
AES_COUNTER_SCRATCH: i32 = 4832


def aes_byte(offset: i32) -> i32:
    return crypt_buffer_get(offset) & 255


def aes_set_byte(offset: i32, value: i32) -> None:
    crypt_buffer_set(offset, value & 255)


def aes_gf_mul(left: i32, right: i32) -> i32:
    a: i32 = left & 255
    b: i32 = right & 255
    result: i32 = 0
    index: i32 = 0
    while index < 8:
        if (b & 1) != 0: result = result ^ a
        high: i32 = a & 128
        a = (a << 1) & 255
        if high != 0: a = a ^ 27
        b = b >> 1
        index = index + 1
    return result & 255


def aes_gf_pow(value: i32, exponent: i32) -> i32:
    result: i32 = 1
    base: i32 = value & 255
    power: i32 = exponent
    while power > 0:
        if (power & 1) != 0: result = aes_gf_mul(result, base)
        base = aes_gf_mul(base, base)
        power = power >> 1
    return result


def aes_rotl_byte(value: i32, amount: i32) -> i32:
    return ((value << amount) | (value >> (8 - amount))) & 255


def aes_sbox(value: i32) -> i32:
    inverse: i32 = 0
    if (value & 255) != 0: inverse = aes_gf_pow(value, 254)
    return (inverse ^ aes_rotl_byte(inverse, 1) ^ aes_rotl_byte(inverse, 2) ^ aes_rotl_byte(inverse, 3) ^ aes_rotl_byte(inverse, 4) ^ 99) & 255


def aes_rcon(round_number: i32) -> i32:
    result: i32 = 1
    index: i32 = 1
    while index < round_number:
        result = aes_gf_mul(result, 2)
        index = index + 1
    return result


def aes_expand_key(key_offset: i32) -> None:
    index: i32 = 0
    while index < 16:
        aes_set_byte(AES_KEY_SCRATCH + index, aes_byte(key_offset + index))
        index = index + 1
    while index < 176:
        temp0: i32 = aes_byte(AES_KEY_SCRATCH + index - 4)
        temp1: i32 = aes_byte(AES_KEY_SCRATCH + index - 3)
        temp2: i32 = aes_byte(AES_KEY_SCRATCH + index - 2)
        temp3: i32 = aes_byte(AES_KEY_SCRATCH + index - 1)
        if index % 16 == 0:
            old0: i32 = temp0
            temp0 = aes_sbox(temp1) ^ aes_rcon(index // 16)
            temp1 = aes_sbox(temp2)
            temp2 = aes_sbox(temp3)
            temp3 = aes_sbox(old0)
        aes_set_byte(AES_KEY_SCRATCH + index, aes_byte(AES_KEY_SCRATCH + index - 16) ^ temp0)
        aes_set_byte(AES_KEY_SCRATCH + index + 1, aes_byte(AES_KEY_SCRATCH + index - 15) ^ temp1)
        aes_set_byte(AES_KEY_SCRATCH + index + 2, aes_byte(AES_KEY_SCRATCH + index - 14) ^ temp2)
        aes_set_byte(AES_KEY_SCRATCH + index + 3, aes_byte(AES_KEY_SCRATCH + index - 13) ^ temp3)
        index = index + 4


def aes_add_round_key(round_number: i32) -> None:
    index: i32 = 0
    while index < 16:
        aes_set_byte(AES_STATE_SCRATCH + index, aes_byte(AES_STATE_SCRATCH + index) ^ aes_byte(AES_KEY_SCRATCH + round_number * 16 + index))
        index = index + 1


def aes_sub_bytes() -> None:
    index: i32 = 0
    while index < 16:
        aes_set_byte(AES_STATE_SCRATCH + index, aes_sbox(aes_byte(AES_STATE_SCRATCH + index)))
        index = index + 1


def aes_shift_rows() -> None:
    row: i32 = 1
    while row < 4:
        first: i32 = aes_byte(AES_STATE_SCRATCH + row)
        second: i32 = aes_byte(AES_STATE_SCRATCH + row + 4)
        third: i32 = aes_byte(AES_STATE_SCRATCH + row + 8)
        fourth: i32 = aes_byte(AES_STATE_SCRATCH + row + 12)
        if row == 1:
            aes_set_byte(AES_STATE_SCRATCH + row, second); aes_set_byte(AES_STATE_SCRATCH + row + 4, third); aes_set_byte(AES_STATE_SCRATCH + row + 8, fourth); aes_set_byte(AES_STATE_SCRATCH + row + 12, first)
        elif row == 2:
            aes_set_byte(AES_STATE_SCRATCH + row, third); aes_set_byte(AES_STATE_SCRATCH + row + 4, fourth); aes_set_byte(AES_STATE_SCRATCH + row + 8, first); aes_set_byte(AES_STATE_SCRATCH + row + 12, second)
        else:
            aes_set_byte(AES_STATE_SCRATCH + row, fourth); aes_set_byte(AES_STATE_SCRATCH + row + 4, first); aes_set_byte(AES_STATE_SCRATCH + row + 8, second); aes_set_byte(AES_STATE_SCRATCH + row + 12, third)
        row = row + 1


def aes_mix_columns() -> None:
    column: i32 = 0
    while column < 4:
        offset: i32 = AES_STATE_SCRATCH + column * 4
        a0: i32 = aes_byte(offset); a1: i32 = aes_byte(offset + 1); a2: i32 = aes_byte(offset + 2); a3: i32 = aes_byte(offset + 3)
        aes_set_byte(offset, aes_gf_mul(a0, 2) ^ aes_gf_mul(a1, 3) ^ a2 ^ a3)
        aes_set_byte(offset + 1, a0 ^ aes_gf_mul(a1, 2) ^ aes_gf_mul(a2, 3) ^ a3)
        aes_set_byte(offset + 2, a0 ^ a1 ^ aes_gf_mul(a2, 2) ^ aes_gf_mul(a3, 3))
        aes_set_byte(offset + 3, aes_gf_mul(a0, 3) ^ a1 ^ a2 ^ aes_gf_mul(a3, 2))
        column = column + 1


def crypt_aes128_encrypt_block(key_offset: i32, input_offset: i32, output_offset: i32) -> i32:
    if not crypt_range_valid(key_offset, 16) or not crypt_range_valid(input_offset, 16) or not crypt_range_valid(output_offset, 16): return -2
    aes_expand_key(key_offset)
    index: i32 = 0
    while index < 16:
        aes_set_byte(AES_STATE_SCRATCH + index, aes_byte(input_offset + index))
        index = index + 1
    aes_add_round_key(0)
    round_number: i32 = 1
    while round_number < 10:
        aes_sub_bytes(); aes_shift_rows(); aes_mix_columns(); aes_add_round_key(round_number)
        round_number = round_number + 1
    aes_sub_bytes(); aes_shift_rows(); aes_add_round_key(10)
    index = 0
    while index < 16:
        aes_set_byte(output_offset + index, aes_byte(AES_STATE_SCRATCH + index))
        index = index + 1
    return 16


def aes_increment_counter() -> None:
    index: i32 = 15
    while index >= 0:
        next_value: i32 = aes_byte(AES_COUNTER_SCRATCH + index) + 1
        aes_set_byte(AES_COUNTER_SCRATCH + index, next_value)
        if next_value <= 255: return
        index = index - 1


def crypt_aes128_ctr(key_offset: i32, counter_offset: i32, input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if not crypt_range_valid(key_offset, 16) or not crypt_range_valid(counter_offset, 16): return -2
    if not crypt_range_valid(input_offset, input_length) or not crypt_range_valid(output_offset, input_length): return -2
    index: i32 = 0
    while index < 16:
        aes_set_byte(AES_COUNTER_SCRATCH + index, aes_byte(counter_offset + index))
        index = index + 1
    aes_expand_key(key_offset)
    processed: i32 = 0
    while processed < input_length:
        index = 0
        while index < 16:
            aes_set_byte(AES_STATE_SCRATCH + index, aes_byte(AES_COUNTER_SCRATCH + index))
            index = index + 1
        aes_add_round_key(0)
        round_number: i32 = 1
        while round_number < 10:
            aes_sub_bytes(); aes_shift_rows(); aes_mix_columns(); aes_add_round_key(round_number)
            round_number = round_number + 1
        aes_sub_bytes(); aes_shift_rows(); aes_add_round_key(10)
        index = 0
        while index < 16 and processed < input_length:
            aes_set_byte(output_offset + processed, aes_byte(input_offset + processed) ^ aes_byte(AES_STATE_SCRATCH + index))
            index = index + 1
            processed = processed + 1
        aes_increment_counter()
    return input_length


def aes128_expected(index: i32) -> i32:
    if index == 0: return 105
    elif index == 1: return 196
    elif index == 2: return 224
    elif index == 3: return 216
    elif index == 4: return 106
    elif index == 5: return 123
    elif index == 6: return 4
    elif index == 7: return 48
    elif index == 8: return 216
    elif index == 9: return 205
    elif index == 10: return 183
    elif index == 11: return 128
    elif index == 12: return 112
    elif index == 13: return 180
    elif index == 14: return 197
    elif index == 15: return 90
    return 0


def crypt_aes128_self_test() -> i32:
    global aes128_self_test_status
    index: i32 = 0
    while index < 16:
        aes_set_byte(index, index)
        aes_set_byte(16 + index, index * 17)
        index = index + 1
    if crypt_aes128_encrypt_block(0, 16, 32) != 16:
        aes128_self_test_status = -1
        return -1
    index = 0
    while index < 16:
        if aes_byte(32 + index) != aes128_expected(index):
            aes128_self_test_status = -1
            return -1
        index = index + 1
    aes128_self_test_status = 1
    return 1