# FIPS 180-4 SHA-256, implemented in pure LPython.
SHA256_SCRATCH: i32 = 4096
sha256_self_test_status: i32 = 0


def sha256_rotr(value: u32, amount: i32) -> u32:
    return (value >> u32(amount)) | (value << (u32(32) - u32(amount)))


def sha256_k(index: i32) -> u32:
    if index == 0: return u32(1116352408)
    elif index == 1: return u32(1899447441)
    elif index == 2: return u32(3049323471)
    elif index == 3: return u32(3921009573)
    elif index == 4: return u32(961987163)
    elif index == 5: return u32(1508970993)
    elif index == 6: return u32(2453635748)
    elif index == 7: return u32(2870763221)
    elif index == 8: return u32(3624381080)
    elif index == 9: return u32(310598401)
    elif index == 10: return u32(607225278)
    elif index == 11: return u32(1426881987)
    elif index == 12: return u32(1925078388)
    elif index == 13: return u32(2162078206)
    elif index == 14: return u32(2614888103)
    elif index == 15: return u32(3248222580)
    elif index == 16: return u32(3835390401)
    elif index == 17: return u32(4022224774)
    elif index == 18: return u32(264347078)
    elif index == 19: return u32(604807628)
    elif index == 20: return u32(770255983)
    elif index == 21: return u32(1249150122)
    elif index == 22: return u32(1555081692)
    elif index == 23: return u32(1996064986)
    elif index == 24: return u32(2554220882)
    elif index == 25: return u32(2821834349)
    elif index == 26: return u32(2952996808)
    elif index == 27: return u32(3210313671)
    elif index == 28: return u32(3336571891)
    elif index == 29: return u32(3584528711)
    elif index == 30: return u32(113926993)
    elif index == 31: return u32(338241895)
    elif index == 32: return u32(666307205)
    elif index == 33: return u32(773529912)
    elif index == 34: return u32(1294757372)
    elif index == 35: return u32(1396182291)
    elif index == 36: return u32(1695183700)
    elif index == 37: return u32(1986661051)
    elif index == 38: return u32(2177026350)
    elif index == 39: return u32(2456956037)
    elif index == 40: return u32(2730485921)
    elif index == 41: return u32(2820302411)
    elif index == 42: return u32(3259730800)
    elif index == 43: return u32(3345764771)
    elif index == 44: return u32(3516065817)
    elif index == 45: return u32(3600352804)
    elif index == 46: return u32(4094571909)
    elif index == 47: return u32(275423344)
    elif index == 48: return u32(430227734)
    elif index == 49: return u32(506948616)
    elif index == 50: return u32(659060556)
    elif index == 51: return u32(883997877)
    elif index == 52: return u32(958139571)
    elif index == 53: return u32(1322822218)
    elif index == 54: return u32(1537002063)
    elif index == 55: return u32(1747873779)
    elif index == 56: return u32(1955562222)
    elif index == 57: return u32(2024104815)
    elif index == 58: return u32(2227730452)
    elif index == 59: return u32(2361852424)
    elif index == 60: return u32(2428436474)
    elif index == 61: return u32(2756734187)
    elif index == 62: return u32(3204031479)
    elif index == 63: return u32(3329325298)
    return u32(0)


def sha256_word_get(index: i32) -> u32:
    offset: i32 = SHA256_SCRATCH + index * 4
    return (u32(crypt_buffer_get(offset) & 255) << u32(24)) | (u32(crypt_buffer_get(offset + 1) & 255) << u32(16)) | (u32(crypt_buffer_get(offset + 2) & 255) << u32(8)) | u32(crypt_buffer_get(offset + 3) & 255)


def sha256_word_set(index: i32, value: u32) -> None:
    offset: i32 = SHA256_SCRATCH + index * 4
    crypt_buffer_set(offset, i32((value >> u32(24)) & u32(255)))
    crypt_buffer_set(offset + 1, i32((value >> u32(16)) & u32(255)))
    crypt_buffer_set(offset + 2, i32((value >> u32(8)) & u32(255)))
    crypt_buffer_set(offset + 3, i32(value & u32(255)))


def sha256_message_byte(input_offset: i32, input_length: i32, position: i32, padded_length: i32) -> i32:
    if position < input_length: return crypt_buffer_get(input_offset + position) & 255
    if position == input_length: return 128
    bit_length: u32 = u32(input_length) * u32(8)
    tail: i32 = padded_length - position
    if tail == 4: return i32((bit_length >> u32(24)) & u32(255))
    if tail == 3: return i32((bit_length >> u32(16)) & u32(255))
    if tail == 2: return i32((bit_length >> u32(8)) & u32(255))
    if tail == 1: return i32(bit_length & u32(255))
    return 0


def crypt_sha256(input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if input_offset < 0 or input_length < 0 or input_offset + input_length > SHA256_SCRATCH: return -2
    if output_offset < 0 or output_offset + 32 > SHA256_SCRATCH: return -2
    padded_length: i32 = ((input_length + 9 + 63) // 64) * 64
    h0: u32 = u32(1779033703); h1: u32 = u32(3144134277)
    h2: u32 = u32(1013904242); h3: u32 = u32(2773480762)
    h4: u32 = u32(1359893119); h5: u32 = u32(2600822924)
    h6: u32 = u32(528734635); h7: u32 = u32(1541459225)
    block: i32 = 0
    while block < padded_length:
        index: i32 = 0
        while index < 16:
            message: i32 = block + index * 4
            word: u32 = (u32(sha256_message_byte(input_offset, input_length, message, padded_length)) << u32(24)) | (u32(sha256_message_byte(input_offset, input_length, message + 1, padded_length)) << u32(16)) | (u32(sha256_message_byte(input_offset, input_length, message + 2, padded_length)) << u32(8)) | u32(sha256_message_byte(input_offset, input_length, message + 3, padded_length))
            sha256_word_set(index, word)
            index = index + 1
        while index < 64:
            previous15: u32 = sha256_word_get(index - 15)
            previous2: u32 = sha256_word_get(index - 2)
            small0: u32 = sha256_rotr(previous15, 7) ^ sha256_rotr(previous15, 18) ^ (previous15 >> u32(3))
            small1: u32 = sha256_rotr(previous2, 17) ^ sha256_rotr(previous2, 19) ^ (previous2 >> u32(10))
            sha256_word_set(index, sha256_word_get(index - 16) + small0 + sha256_word_get(index - 7) + small1)
            index = index + 1
        a: u32 = h0; b: u32 = h1; c: u32 = h2; d: u32 = h3
        e: u32 = h4; f: u32 = h5; g: u32 = h6; h: u32 = h7
        index = 0
        while index < 64:
            big1: u32 = sha256_rotr(e, 6) ^ sha256_rotr(e, 11) ^ sha256_rotr(e, 25)
            choose: u32 = (e & f) ^ (bitnot_u32(e) & g)
            temporary1: u32 = h + big1 + choose + sha256_k(index) + sha256_word_get(index)
            big0: u32 = sha256_rotr(a, 2) ^ sha256_rotr(a, 13) ^ sha256_rotr(a, 22)
            majority: u32 = (a & b) ^ (a & c) ^ (b & c)
            temporary2: u32 = big0 + majority
            h = g; g = f; f = e; e = d + temporary1
            d = c; c = b; b = a; a = temporary1 + temporary2
            index = index + 1
        h0 = h0 + a; h1 = h1 + b; h2 = h2 + c; h3 = h3 + d
        h4 = h4 + e; h5 = h5 + f; h6 = h6 + g; h7 = h7 + h
        block = block + 64
    sha256_word_set(64, h0); sha256_word_set(65, h1); sha256_word_set(66, h2); sha256_word_set(67, h3)
    sha256_word_set(68, h4); sha256_word_set(69, h5); sha256_word_set(70, h6); sha256_word_set(71, h7)
    index = 0
    while index < 32:
        crypt_buffer_set(output_offset + index, crypt_buffer_get(SHA256_SCRATCH + 256 + index))
        index = index + 1
    return 32



def sha256_empty_expected(index: i32) -> i32:
    if index == 0: return 227
    elif index == 1: return 176
    elif index == 2: return 196
    elif index == 3: return 66
    elif index == 4: return 152
    elif index == 5: return 252
    elif index == 6: return 28
    elif index == 7: return 20
    elif index == 8: return 154
    elif index == 9: return 251
    elif index == 10: return 244
    elif index == 11: return 200
    elif index == 12: return 153
    elif index == 13: return 111
    elif index == 14: return 185
    elif index == 15: return 36
    elif index == 16: return 39
    elif index == 17: return 174
    elif index == 18: return 65
    elif index == 19: return 228
    elif index == 20: return 100
    elif index == 21: return 155
    elif index == 22: return 147
    elif index == 23: return 76
    elif index == 24: return 164
    elif index == 25: return 149
    elif index == 26: return 153
    elif index == 27: return 27
    elif index == 28: return 120
    elif index == 29: return 82
    elif index == 30: return 184
    elif index == 31: return 85
    return 0

def sha256_abc_expected(index: i32) -> i32:
    if index == 0: return 186
    elif index == 1: return 120
    elif index == 2: return 22
    elif index == 3: return 191
    elif index == 4: return 143
    elif index == 5: return 1
    elif index == 6: return 207
    elif index == 7: return 234
    elif index == 8: return 65
    elif index == 9: return 65
    elif index == 10: return 64
    elif index == 11: return 222
    elif index == 12: return 93
    elif index == 13: return 174
    elif index == 14: return 34
    elif index == 15: return 35
    elif index == 16: return 176
    elif index == 17: return 3
    elif index == 18: return 97
    elif index == 19: return 163
    elif index == 20: return 150
    elif index == 21: return 23
    elif index == 22: return 122
    elif index == 23: return 156
    elif index == 24: return 180
    elif index == 25: return 16
    elif index == 26: return 255
    elif index == 27: return 97
    elif index == 28: return 242
    elif index == 29: return 0
    elif index == 30: return 21
    elif index == 31: return 173
    return 0

def sha256_self_test_vector(length: i32, expected_offset: i32) -> i32:
    result: i32 = crypt_sha256(0, length, 128)
    if result != 32: return 0
    index: i32 = 0
    while index < 32:
        if crypt_buffer_get(128 + index) != crypt_buffer_get(expected_offset + index): return 0
        index = index + 1
    return 1


def crypt_sha256_self_test() -> i32:
    # FIPS 180-4/SHA-256 known-answer tests: empty input and ASCII "abc".
    global sha256_self_test_status
    index: i32 = 0
    while index < 32:
        crypt_buffer_set(index, 0)
        crypt_buffer_set(64 + index, 0)
        index = index + 1
    # Expected digests are stored inline to avoid depending on a runtime allocator.
    index = 0
    while index < 32:
        crypt_buffer_set(64 + index, sha256_empty_expected(index))
        crypt_buffer_set(96 + index, sha256_abc_expected(index))
        index = index + 1
    if sha256_self_test_vector(0, 64) == 0:
        sha256_self_test_status = -1
        return -1
    crypt_buffer_set(0, 97)
    crypt_buffer_set(1, 98)
    crypt_buffer_set(2, 99)
    if sha256_self_test_vector(3, 96) == 0:
        sha256_self_test_status = -1
        return -1
    sha256_self_test_status = 1
    return 1