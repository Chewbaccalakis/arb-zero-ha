"""Protocol tests using packets captured from the ARB app."""




from custom_components.arb_zero import protocol as p

h = bytes.fromhex


def test_status_request():
    assert p.build_status_request() == h("aac1f0000000000000000000000000 5c".replace(" ", ""))


def test_commands_match_capture():
    cases = [
        (p.Setting.SETPOINT, -6, "aac1f1000000 00fa0001000000000058"),
        (p.Setting.SETPOINT, -7, "aac1f1000000 00f90001000000000057"),
        (p.Setting.BOOST, 1, "aac1f1000100 00000003000000000061"),
        (p.Setting.BOOST, 0, "aac1f1000000 00000003000000000060"),
        (p.Setting.DISPLAY_UNIT, 1, "aac1f1000001 00000004000000000062"),
        (p.Setting.DISPLAY_UNIT, 0, "aac1f1000000 00000004000000000061"),
        (p.Setting.BATTERY_PROTECTION, 0, "aac1f1000000 00000005000000000062"),
        (p.Setting.BATTERY_PROTECTION, 1, "aac1f1000000 01000005000000000063"),
        (p.Setting.BATTERY_PROTECTION, 2, "aac1f1000000 02000005000000000064"),
    ]
    for setting, value, expected in cases:
        assert p.build_command(setting, value) == h(expected.replace(" ", "")), setting


def test_parse_status():
    s = p.parse_status(h("aac1f2a00305f9f800000a0d0000000e"))
    assert (s.temperature, s.setpoint, s.boost, s.fahrenheit) == (-7, -8, True, True)
    assert s.battery_protection == "low"
    assert p.parse_status(h("aac1f2a00705faf900000a0c00000013")).battery_protection == "medium"
    assert p.parse_status(h("aac1f2a00b05faf900000a0c00000017")).battery_protection == "high"


def test_parse_rejects_bad_packets():
    assert p.parse_status(h("aac1f2a00305f9f800000a0d0000000f")) is None  # checksum
    assert p.parse_status(h("aac1f0000000000000000000000000 5c".replace(" ", ""))) is None
    assert p.parse_status(b"\xaa\xc1") is None
