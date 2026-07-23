# SHA-256 counter DRBG. It has no hardware entropy source: callers must seed it.
CRYPT_DRBG_STATE: i32 = 4400
CRYPT_DRBG_INPUT: i32 = 3840
CRYPT_DRBG_OUTPUT: i32 = 3904
crypt_drbg_counter: i32 = 0
crypt_drbg_seeded: i32 = 0


def crypt_random_seed(input_offset: i32, input_length: i32) -> i32:
    global crypt_drbg_counter, crypt_drbg_seeded
    if not crypt_range_valid(input_offset, input_length) or input_length < 16: return -2
    if sha256_self_test_status != 1: return -9
    if crypt_sha256(input_offset, input_length, CRYPT_DRBG_OUTPUT) != 32: return -3
    index: i32 = 0
    while index < 32:
        crypt_buffer_set(CRYPT_DRBG_STATE + index, crypt_buffer_get(CRYPT_DRBG_OUTPUT + index))
        index = index + 1
    crypt_drbg_counter = 0
    crypt_drbg_seeded = 1
    return 0


def crypt_random_next_block() -> i32:
    global crypt_drbg_counter
    if crypt_drbg_seeded == 0: return -8
    index: i32 = 0
    while index < 32:
        crypt_buffer_set(CRYPT_DRBG_INPUT + index, crypt_buffer_get(CRYPT_DRBG_STATE + index))
        index = index + 1
    crypt_buffer_set(CRYPT_DRBG_INPUT + 32, (crypt_drbg_counter >> 24) & 255)
    crypt_buffer_set(CRYPT_DRBG_INPUT + 33, (crypt_drbg_counter >> 16) & 255)
    crypt_buffer_set(CRYPT_DRBG_INPUT + 34, (crypt_drbg_counter >> 8) & 255)
    crypt_buffer_set(CRYPT_DRBG_INPUT + 35, crypt_drbg_counter & 255)
    crypt_drbg_counter = crypt_drbg_counter + 1
    if crypt_sha256(CRYPT_DRBG_INPUT, 36, CRYPT_DRBG_OUTPUT) != 32: return -3
    index = 0
    while index < 32:
        crypt_buffer_set(CRYPT_DRBG_STATE + index, crypt_buffer_get(CRYPT_DRBG_OUTPUT + index))
        index = index + 1
    return 32


def crypt_random_bytes(output_offset: i32, output_length: i32) -> i32:
    if not crypt_range_valid(output_offset, output_length): return -2
    written: i32 = 0
    while written < output_length:
        if crypt_random_next_block() != 32: return -8
        index: i32 = 0
        while index < 32 and written < output_length:
            crypt_buffer_set(output_offset + written, crypt_buffer_get(CRYPT_DRBG_OUTPUT + index))
            index = index + 1
            written = written + 1
    return written