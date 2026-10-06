"""ARB Zero Bluetooth protocol.

Reverse-engineered from the ARB Zero Fridge Connect app. Every packet is
16 bytes: ``AA C1 <type> <12 data bytes> <checksum>``, where the checksum is
``(sum of the first 15 bytes + 1) & 0xFF``.

The app writes to FFF6 and the fridge answers with notifications on FFF7.
The fridge sends nothing unless asked, so status must be polled.

    AA C1 F0 ...  status request
    AA C1 F2 ...  status reply
        [4] flags: bits 2-3 battery protection (0 low, 1 medium, 2 high);
                   bits 0-1 boost and degrees F (see BOOST_BIT/FAHRENHEIT_BIT)
        [6] cabinet temperature, signed, in the display unit
        [7] setpoint, signed, in the display unit
    AA C1 F1 ...  settings command; [9] selects the setting:
        01 setpoint            value in [7]
        03 boost               value in [4] (0 off, 1 on)
        04 display unit        value in [5] (0 C, 1 F)
        05 battery protection  value in [6] (0 low, 1 medium, 2 high)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fff6-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff7-0000-1000-8000-00805f9b34fb"

HEADER = (0xAA, 0xC1)
TYPE_STATUS_REQUEST = 0xF0
TYPE_COMMAND = 0xF1
TYPE_STATUS_REPLY = 0xF2
PACKET_LENGTH = 16

# Both bits were always set in the captures, so this pairing is unconfirmed.
BOOST_BIT = 0
FAHRENHEIT_BIT = 1


class Setting(IntEnum):
    """Setting selector (byte 9) and the byte that carries its value."""

    SETPOINT = 0x01
    BOOST = 0x03
    DISPLAY_UNIT = 0x04
    BATTERY_PROTECTION = 0x05


VALUE_INDEX = {
    Setting.SETPOINT: 7,
    Setting.BOOST: 4,
    Setting.DISPLAY_UNIT: 5,
    Setting.BATTERY_PROTECTION: 6,
}

BATTERY_LEVELS = ("low", "medium", "high")


def checksum(data: bytes | bytearray) -> int:
    """Return the checksum for the first 15 bytes of a packet."""
    return (sum(data[:15]) + 1) & 0xFF


def _frame(packet_type: int, body: bytearray | None = None) -> bytes:
    packet = bytearray(15)
    packet[0], packet[1] = HEADER
    packet[2] = packet_type
    if body is not None:
        packet[3:15] = body[3:15]
    return bytes(packet) + bytes([checksum(packet)])


def build_status_request() -> bytes:
    """Return the packet that asks the fridge for its status."""
    return _frame(TYPE_STATUS_REQUEST)


def build_command(setting: Setting, value: int) -> bytes:
    """Return the packet that changes one setting."""
    body = bytearray(15)
    body[VALUE_INDEX[setting]] = value & 0xFF
    body[9] = int(setting)
    return _frame(TYPE_COMMAND, body)


def _signed(value: int) -> int:
    return value - 256 if value > 127 else value


@dataclass(frozen=True)
class ArbZeroStatus:
    """Decoded status reply."""

    temperature: int
    setpoint: int
    fahrenheit: bool
    boost: bool
    battery_protection: str | None
    raw: bytes

    @property
    def raw_byte_11(self) -> int:
        """Unknown value, possibly related to supply voltage."""
        return self.raw[11]


def parse_status(data: bytes | bytearray) -> ArbZeroStatus | None:
    """Decode a status reply, or return None if it isn't one."""
    if (
        len(data) < PACKET_LENGTH
        or tuple(data[:2]) != HEADER
        or data[2] != TYPE_STATUS_REPLY
        or checksum(data) != data[15]
    ):
        return None
    flags = data[4]
    level = (flags >> 2) & 0x03
    return ArbZeroStatus(
        temperature=_signed(data[6]),
        setpoint=_signed(data[7]),
        fahrenheit=bool(flags >> FAHRENHEIT_BIT & 1),
        boost=bool(flags >> BOOST_BIT & 1),
        battery_protection=BATTERY_LEVELS[level] if level < 3 else None,
        raw=bytes(data[:PACKET_LENGTH]),
    )
