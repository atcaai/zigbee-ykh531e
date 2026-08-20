# tuya_encoder.py
import base64
import struct


def encode_ir(ir_message: bytes) -> str:
    """
    Encodes a 13-byte YK-H/531E packet into the Tuya 0x07 0x34 compressed IR format.
    """
    # 1. Tuya Header + 4 Primary Protocol Timings (Big Endian uint16)
    payload = bytearray([0x07, 0x34])
    payload.extend(struct.pack(">H", 9100))  # Header Mark
    payload.extend(struct.pack(">H", 4500))  # Header Space
    payload.extend(struct.pack(">H", 600))   # Bit Mark / Zero Space
    payload.extend(struct.pack(">H", 1700))  # One Space

    # 2. Encode Bitstream
    # Tuya packs bit timings into compressed sequence bytes
    bit_buffer = 0
    bits_in_buffer = 0

    # Add header sequence
    seq = [0, 1]  # Header mark, Header space
    
    # Add data bit sequence
    for byte in ir_message:
        for j in range(8):
            bit = (byte >> j) & 1
            if bit:
                seq.extend([2, 3])  # Bit mark, One space
            else:
                seq.extend([2, 2])  # Bit mark, Zero space
    seq.append(2)  # Footer mark

    # 3. Pack 2-bit symbol indices into bytes
    for symbol in seq:
        bit_buffer = (bit_buffer << 2) | symbol
        bits_in_buffer += 2
        if bits_in_buffer >= 8:
            bits_in_buffer -= 8
            payload.append((bit_buffer >> bits_in_buffer) & 0xFF)

    if bits_in_buffer > 0:
        payload.append((bit_buffer << (8 - bits_in_buffer)) & 0xFF)

    return base64.b64encode(payload).decode("ascii")
