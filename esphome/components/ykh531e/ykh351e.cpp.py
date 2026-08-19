import logging
from typing import List, Optional

logger = logging.getLogger("ykh531e.climate")

# Constants mapping
YKH531E_TEMP_MIN = 16.0
YKH531E_TEMP_MAX = 32.0
YKH531E_TEMP_INC = 1.0

YKH531E_FAN_SPEED_LOW = 0b011
YKH531E_FAN_SPEED_MID = 0b010
YKH531E_FAN_SPEED_HIGH = 0b001
YKH531E_FAN_SPEED_AUTO = 0b101

YKH531E_SWING_ON = 0b000
YKH531E_SWING_OFF = 0b111

YKH531E_MODE_AUTO = 0b000
YKH531E_MODE_COOL = 0b001
YKH531E_MODE_DRY = 0b010
YKH531E_MODE_HEAT = 0b100
YKH531E_MODE_FAN = 0b110


def encode_temperature_celsius(temperature: float) -> int:
    """Encode target temperature in Celsius for the protocol."""
    if temperature > YKH531E_TEMP_MAX:
        return int(YKH531E_TEMP_MAX - 8)
    if temperature < YKH531E_TEMP_MIN:
        return int(YKH531E_TEMP_MIN - 8)
    return int(temperature - 8)


def decode_temperature_celsius(encoded_temperature: int) -> float:
    """Decode protocol temperature byte back to Celsius."""
    return float(encoded_temperature + 8.0)


def encode_temperature_fahrenheit(temperature_c: float) -> int:
    """Convert Celsius to Fahrenheit and apply protocol offset."""
    temp_f = temperature_c * 9.0 / 5.0 + 32.0
    if temp_f > 90.0:
        temp_f = 90.0
    if temp_f < 60.0:
        temp_f = 60.0
    return int(temp_f) + 8


class YKH531EClimateState:
    """Represents climate configuration parameters for state serialization."""
    def __init__(self):
        self.mode = "off"
        self.target_temperature = 21.0
        self.fan_mode = "auto"
        self.swing_mode = "off"
        self.preset = "none"
        self.transmit_fahrenheit = False
        self.supports_heat = True


def build_ykh531e_packet(state: YKH531EClimateState) -> bytearray:
    """Serializes climate state into the 13-byte YK-H/531E infrared payload."""
    ir_message = bytearray(13)

    # Byte 0: Preamble
    ir_message[0] = 0b11000011

    # Byte 1: Swing mode and Celsius temperature
    if state.swing_mode == "vertical":
        ir_message[1] |= YKH531E_SWING_ON
    else:
        ir_message[1] |= YKH531E_SWING_OFF

    if state.mode not in ["fan_only", "dry"]:
        if state.transmit_fahrenheit:
            logger.debug("Transmitting in Fahrenheit mode")
            temp_f_encoded = encode_temperature_fahrenheit(state.target_temperature)
            temp_f = state.target_temperature * 9.0 / 5.0 + 32.0
            logger.debug("Target %.1f C = %.1f F, encoded as %d", state.target_temperature, temp_f, temp_f_encoded)
            ir_message[10] |= (temp_f_encoded << 1) & 0b11111110
        else:
            logger.debug("Transmitting in Celsius mode")
            ir_message[1] |= encode_temperature_celsius(state.target_temperature) << 3
    else:
        logger.debug("Mode %s does not use temperature, skipping temperature encoding", state.mode)

    # Byte 4: Fan speed bits (bits 5-7)
    fan_mapping = {
        "low": YKH531E_FAN_SPEED_LOW,
        "medium": YKH531E_FAN_SPEED_MID,
        "high": YKH531E_FAN_SPEED_HIGH,
        "auto": YKH531E_FAN_SPEED_AUTO
    }
    fan_val = fan_mapping.get(state.fan_mode, YKH531E_FAN_SPEED_AUTO)
    ir_message[4] |= fan_val << 5

    # Byte 6: Preset, Fahrenheit flag, and operation mode
    if state.preset == "sleep":
        ir_message[6] |= 1 << 2
    if state.transmit_fahrenheit:
        ir_message[6] |= 0b00000010

    mode_mapping = {
        "auto": YKH531E_MODE_AUTO,
        "cool": YKH531E_MODE_COOL,
        "dry": YKH531E_MODE_DRY,
        "heat": YKH531E_MODE_HEAT,
        "fan_only": YKH531E_MODE_FAN
    }
    mode_val = mode_mapping.get(state.mode, YKH531E_MODE_AUTO)
    if state.mode == "heat":
        logger.info("Heat mode is experimental and may not work on all units.")
    ir_message[6] |= mode_val << 5

    # Byte 9: Power state (bit 5)
    if state.mode != "off":
        ir_message[9] |= 1 << 5

    # Byte 12: Checksum (sum of bytes 0 through 11)
    checksum = sum(ir_message[:12]) & 0xFF
    ir_message[12] = checksum

    return ir_message


def parse_ykh531e_packet(ir_message: bytes) -> Optional[YKH531EClimateState]:
    """Validates checksum and decodes a 13-byte payload back into climate state."""
    if len(ir_message) < 13:
        return None

    # Validate checksum
    checksum = sum(ir_message[:12]) & 0xFF
    if ir_message[12] != checksum:
        logger.debug("Checksum fail")
        return None

    state = YKH531EClimateState()
    power = (ir_message[9] & 0b00100000) >> 5
    if not power:
        state.mode = "off"
        return state

    vertical_swing = ir_message[1] & 0b00000111
    state.swing_mode = "vertical" if vertical_swing == YKH531E_SWING_ON else "off"

    fan_speed = (ir_message[4] & 0b11100000) >> 5
    reverse_fan_mapping = {
        YKH531E_FAN_SPEED_LOW: "low",
        YKH531E_FAN_SPEED_MID: "medium",
        YKH531E_FAN_SPEED_HIGH: "high",
        YKH531E_FAN_SPEED_AUTO: "auto"
    }
    state.fan_mode = reverse_fan_mapping.get(fan_speed, "auto")

    state.preset = "sleep" if (ir_message[6] & 0b00000100) else "none"

    mode_bits = (ir_message[6] & 0b11100000) >> 5
    reverse_mode_mapping = {
        YKH531E_MODE_AUTO: "auto",
        YKH531E_MODE_COOL: "cool",
        YKH531E_MODE_DRY: "dry",
        YKH531E_MODE_HEAT: "heat",
        YKH531E_MODE_FAN: "fan_only"
    }
    state.mode = reverse_mode_mapping.get(mode_bits, "auto")

    if state.mode not in ["fan_only", "dry"]:
        fahrenheit = bool((ir_message[6] & 0b00000010) >> 1)
        state.transmit_fahrenheit = fahrenheit
        if fahrenheit:
            temp_f = ((ir_message[10] & 0b11111110) >> 1) - 8
            state.target_temperature = (temp_f - 32) * 5.0 / 9.0
        else:
            temp_c = decode_temperature_celsius((ir_message[1] & 0b11111000) >> 3)
            state.target_temperature = temp_c

    return state
