"""
YK-H/531E Air Conditioner Remote Control Protocol Constants and Encoder Structure
Source references:
- https://blog.spans.fi/2024/04/16/reverse-engineering-the-yk-h531e-ac-remote-control-ir-protocol.html[span_0](start_span)[span_0](end_span)
- https://github.com/crankyoldgit/IRremoteESP8266/blob/master/src/ir_Electra.h[span_1](start_span)[span_1](end_span)
- https://github.com/iverasp/esphome/tree/ykh531e[span_2](start_span)[span_2](end_span)
Tested on: Frigidaire FHPC102AC1[span_3](start_span)[span_3](end_span)
"""

from dataclasses import dataclass, field
from typing import List

# Protocol constants
YKH531E_IR_FREQUENCY = 38000

# Timings in microseconds
YKH531E_HEADER_MARK = 9100
YKH531E_HEADER_SPACE = 4500
YKH531E_BIT_MARK = 600
YKH531E_ZERO_SPACE = 600
YKH531E_ONE_SPACE = 1700

# Fan speed codes
YKH531E_FAN_SPEED_LOW = 0b011
YKH531E_FAN_SPEED_MID = 0b010
YKH531E_FAN_SPEED_HIGH = 0b001
YKH531E_FAN_SPEED_AUTO = 0b101

# Swing codes
YKH531E_SWING_ON = 0b000
YKH531E_SWING_OFF = 0b111

# Mode codes
YKH531E_MODE_AUTO = 0b000
YKH531E_MODE_COOL = 0b001
YKH531E_MODE_DRY = 0b010
YKH531E_MODE_HEAT = 0b100  # Experimental - some units support this
YKH531E_MODE_FAN = 0b110

# Temperature range
YKH531E_TEMP_MIN = 16.0
YKH531E_TEMP_MAX = 32.0
YKH531E_TEMP_INC = 1.0


@dataclass
class YKH531EClimate:
    """YKH531E Climate IR remote control handler.
    
    Note: Only vertical swing is supported by the hardware.
    Heat mode is experimental and may not work on all units.
    """
    temp_min: float = YKH531E_TEMP_MIN
    temp_max: float = YKH531E_TEMP_MAX
    temp_inc: float = YKH531E_TEMP_INC
    supports_heat: bool = True
    supports_cool: bool = True
    fan_modes: List[str] = field(default_factory=lambda: ["auto", "low", "medium", "high"])
    swing_modes: List[str] = field(default_factory=lambda: ["off", "vertical"])
    presets: List[str] = field(default_factory=lambda: ["none", "sleep"])
    transmit_fahrenheit: bool = False

    def set_fahrenheit(self, fahrenheit: bool) -> None:
        """Set use of Fahrenheit units."""
        self.transmit_fahrenheit = fahrenheit

    def traits(self):
        """Override traits to provide specific climate operational constraints."""
        raise NotImplementedError("Subclasses or implementation must provide traits logic.")

    def transmit_state(self) -> None:
        """Transmit current climate state over IR."""
        raise NotImplementedError("Subclasses or implementation must provide transmission logic.")

    def on_receive(self, data) -> bool:
        """Handle incoming IR receive data."""
        raise NotImplementedError("Subclasses or implementation must provide reception logic.")
