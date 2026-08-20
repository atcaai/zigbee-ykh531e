# enocde_34.py
# Replacing LZ77 compression with Tuya's native 0x07 0x34 symbol index container format for strict AC timing tolerances.

import base64
import struct

def encode_34(ir_message: bytes) -> str:
    """
    Encodes 13-byte YK-H/531E packet into authentic Tuya 0x07 0x34 Base64.
    """
    # 1. Header + 4 Big-Endian Microsecond Lookup Entries
    payload = bytearray([0x07, 0x34])
    payload.extend(struct.pack(">H", 9076))  # Header Mark
    payload.extend(struct.pack(">H", 4395))  # Header Space
    payload.extend(struct.pack(">H", 671))   # Bit Mark / Zero Space
    payload.extend(struct.pack(">H", 1664))  # One Space

    # 2. Build 2-bit symbol index array
    symbols = [0, 1]  # Header mark (0), Header space (1)
    for byte in ir_message:
        for j in range(8):
            bit = (byte >> j) & 1
            if bit:
                symbols.extend([2, 3])  # Bit Mark (2), One Space (3)
            else:
                symbols.extend([2, 2])  # Bit Mark (2), Zero Space (2)
    symbols.append(2)  # Footer mark

    # 3. Pack 2-bit symbols LSB-first to match Tuya hardware decoders
    packed_bytes = bytearray()
    bit_buf = 0
    bits_cnt = 0
    for s in symbols:
        bit_buf |= ((s & 0x03) << bits_cnt)
        bits_cnt += 2
        if bits_cnt == 8:
            packed_bytes.append(bit_buf)
            bit_buf = 0
            bits_cnt = 0

    if bits_cnt > 0:
        packed_bytes.append(bit_buf)

    payload.extend(packed_bytes)
    return base64.b64encode(payload).decode("ascii")
