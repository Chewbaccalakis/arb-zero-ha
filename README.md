# ARB Zero Fridge for Home Assistant

A Home Assistant integration for ARB Zero fridge freezers. It talks to the fridge locally over Bluetooth, either from the Home Assistant host's adapter or through an ESPHome Bluetooth proxy. No cloud is involved.

This project isn't affiliated with or endorsed by ARB. The protocol was worked out from Bluetooth captures of the official app.

## Features

- **Automatic discovery:** any fridge advertising as `ARBZERO` shows up under **Settings → Devices & services → Discovered**.
- **Bluetooth proxy support:** works through any connectable proxy, such as ESPHome with `active: true`.

| Entity | Type | Notes |
|---|---|---|
| Temperature | sensor | Cabinet temperature |
| Setpoint | number | Target temperature |
| Boost | switch | Fast cool-down |
| Battery protection | select | Low / Medium / High |
| Display unit | select | °C / °F on the fridge's display (Home Assistant still converts to your units) |
| Raw byte 11 | sensor | Diagnostic, disabled by default. Not decoded yet. |

## Requirements

- Home Assistant 2025.1 or newer, with Bluetooth set up.
- A **connectable** Bluetooth adapter or proxy within range of the fridge. For an ESPHome proxy, make sure active connections are enabled:

  ```yaml
  bluetooth_proxy:
    active: true
  ```

  Each proxy can hold three active connections, and this integration keeps one of them open.
- The fridge's Bluetooth must be **ON**, and its connection setting must be **OPEN** (not CLO). See the fridge manual.
- The fridge accepts only one connection at a time. Close the ARB app, and remove any ESPHome `ble_client` that connects to the fridge.

## Installation

### HACS

1. In HACS, open the three-dot menu and choose **Custom repositories**.
2. Add this repository's URL with type **Integration**.
3. Install **ARB Zero Fridge**, then restart Home Assistant.

### Manual

Copy `custom_components/arb_zero` into your Home Assistant `config/custom_components/` folder, then restart Home Assistant.

## Setup

When the fridge is in range of a connectable adapter or proxy, it appears under **Discovered**. Click **Add**. You can also add **ARB Zero Fridge** manually from **Add integration** and pick the fridge from the list.

## Known gaps

- In the status reply, Boost and °F are bits 0 and 1 of byte 4. Both were set in every capture, so which bit is which is a guess. If the Boost switch and the display unit seem swapped, change `BOOST_BIT` and `FAHRENHEIT_BIT` in `protocol.py` and open an issue.
- Only single-zone fridges have been tested. On a dual-zone Zero, the second zone may be in bytes 8–9 of the status reply.
- Byte 11 drifts between about 9 and 17. It may be the supply voltage.

## Protocol

The full protocol is documented in [`protocol.py`](custom_components/arb_zero/protocol.py).

## Development

```sh
pip install pytest-homeassistant-custom-component
pytest
```

The tests use packets captured from a real fridge.
