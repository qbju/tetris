# Pure-LPython cryptography extension API.
CRYPT_PERMISSION_HASH: i32 = 4096
CRYPT_PERMISSION_ENCODING: i32 = 8192
CRYPT_PERMISSION_RANDOM: i32 = 16384
CRYPT_PERMISSION_SYMMETRIC: i32 = 32768
CRYPT_PERMISSION_PQC: i32 = 65536
CRYPT_PERMISSION_LEGACY: i32 = 131072
CRYPT_PERMISSION_ANY: i32 = 258048
CRYPT_BUFFER_SIZE: i32 = 8192
CRYPT_PUBLIC_SIZE: i32 = 3840
aes128_self_test_status: i32 = 0


def crypt_range_valid(offset: i32, length: i32) -> bool:
    return offset >= 0 and length >= 0 and offset <= CRYPT_PUBLIC_SIZE and length <= CRYPT_PUBLIC_SIZE - offset


def extension_crypt_buffer_get(offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_ANY) == 0: return -1
    if not crypt_range_valid(offset, 1): return -2
    return crypt_buffer_get(offset) & 255


def extension_crypt_buffer_set(offset: i32, value: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_ANY) == 0: return -1
    if not crypt_range_valid(offset, 1) or value < 0 or value > 255: return -2
    crypt_buffer_set(offset, value)
    return 0


def extension_crypt_base64_encode(input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_ENCODING) == 0: return -1
    return crypt_base64_encode(input_offset, input_length, output_offset)


def extension_crypt_base64_decode(input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_ENCODING) == 0: return -1
    return crypt_base64_decode(input_offset, input_length, output_offset)

def extension_crypt_sha256(input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_HASH) == 0: return -1
    return crypt_sha256(input_offset, input_length, output_offset)

def extension_crypt_random_seed(input_offset: i32, input_length: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_RANDOM) == 0: return -1
    return crypt_random_seed(input_offset, input_length)


def extension_crypt_random_bytes(output_offset: i32, output_length: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_RANDOM) == 0: return -1
    return crypt_random_bytes(output_offset, output_length)


def extension_crypt_aes128_ctr(key_offset: i32, counter_offset: i32, input_offset: i32, input_length: i32, output_offset: i32) -> i32:
    if extension_current_id < 0 or (extension_current_permissions & CRYPT_PERMISSION_SYMMETRIC) == 0: return -1
    if aes128_self_test_status != 1: return -9
    return crypt_aes128_ctr(key_offset, counter_offset, input_offset, input_length, output_offset)