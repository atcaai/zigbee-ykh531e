# Import the unified module components
from ykh531e import YKH531EClimateState, build_ykh531e_packet, parse_ykh531e_packet
from packet_to_timings import packet_to_timings

# 1. Create and configure a target state
state = YKH531EClimateState()
state.mode = "cool"
state.target_temperature = 22.0
state.fan_mode = "medium"
state.swing_mode = "vertical"

# 2. Build the 13-byte IR packet for transmission
packet = build_ykh531e_packet(state)
print("Generated IR Packet (Hex):", packet.hex(" ").upper())

# 3. Convert the packet into a Tuya and Zosung Zigbee IR devices coded raw timing array from the ir_message bytearray 
packet = build_ykh531e_packet(state)
raw_timings = packet_to_timings(packet)
print("Generated IR timing code (Raw):", raw_timings)

# 4. Parse an incoming packet back into a state object
decoded_state = parse_ykh531e_packet(packet)
if decoded_state:
    print(f"Decoded Mode: {decoded_state.mode}")
    print(f"Decoded Target Temp: {decoded_state.target_temperature}°C")
