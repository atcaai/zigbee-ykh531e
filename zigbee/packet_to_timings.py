def packet_to_timings(ir_message: bytes) -> list[int]:
    """Expands 13-byte YK-H/531E payload into microsecond mark/space timings."""
    # Header timings (Mark, Space)
    timings = [9100, 4500]
    
    # Data bits (LSB first based on encoder implementation)
    for byte in ir_message:
        for j in range(8):
            bit = (byte >> j) & 1
            space = 1700 if bit else 600
            timings.extend([600, space])
            
    # Footer timing (Final mark)
    timings.append(600)
    return timings

# Example usage:
# packet = build_ykh531e_packet(state)
# raw_timings = packet_to_timings(packet)
