# INT-14S-BW Read-Only LAN

INT-14S-BW uses a different Tuya temperature payload layout from INT-14-BW. A successful LAN connection does not make the INT-14-BW decoder compatible with it.

If an INT-14S is configured with the INT-14-BW profile, Home Assistant may show values such as 800 C, negative hundreds of degrees or a base temperature in the thousands. It may also create only two temperature channels per probe instead of the expected five. Those values are parser mismatch artifacts. They are not real readings and must not be corrected with calibration.

## What Was Validated

The beta.6 read-only diagnostic captured INT-14S DP109 from real hardware. It contains:

- four 13-byte probe blocks;
- two-byte station temperature;
- one trailing CRC-8/ATM byte, using polynomial `0x07` and initial value `0x00`.

The first 54 bytes use the same field order, scales and unavailable-probe sentinels as the community-validated BLE FF01 frame. The submitted LAN and BLE readings matched value for value.

## Testing Beta.7

Stable `v0.2.6` enables experimental read-only Tuya LAN temperatures:

1. Install the latest stable release through HACS and restart Home Assistant.
2. Select the correct `INT-14S-BW` model profile.
3. Enter the station host/IP, device ID, local key and protocol version in the integration options.
4. Select `Wi-Fi LAN only` for a clear LAN-only test, or leave `Auto` to prefer the configured LAN path.
5. Confirm that station temperature and all five channels of each active probe remain plausible.
6. Dock or undock one probe and confirm its five temperature entities become unavailable or available together.
7. Download the integration diagnostics and check `int14s_lan_crc8_valid`.
8. Inspect the file before sharing it, then attach the sanitized JSON to the existing INT-14S validation Discussion.

Discussion:

<https://github.com/zampix1/ha-inkbird-int14/discussions/2>

## What It Sends

The capture performs the same class of local Tuya state queries used for polling:

- one status request;
- one requested-DP refresh.

The diagnostic button does not call setting-write functions and does not apply its captured values to Home Assistant entities. The normal polling path applies only supported DPs after validating their type, length and CRC where applicable.

## What It Records

The diagnostics include:

- whether each read query succeeded;
- returned DP numbers;
- numeric and boolean DP values;
- recognized encoded thermometer payloads as hexadecimal;
- type, length and SHA-256 metadata instead of arbitrary strings or unknown binary content.

The capture does not include the configured host, device ID or local key. Home Assistant diagnostics also apply the integration's normal identifier and credential redaction. You should still inspect the file before posting it publicly.

## Current Boundary

INT-14S DP109 temperatures, DP103 station/probe battery percentages and DP104 display brightness are enabled read-only over LAN. The encoded temperature and battery payloads must have the expected length and a valid CRC before any entity is updated; brightness must be an integer from 1 to 100. DP122-125 target blocks are parsed only when their length and CRC are valid. Charging, alarm state, timer, preset, calibration and sound DPs remain unmapped.

All normal INT-14S writes remain blocked. The disabled-by-default BLE C/F validation buttons are a separate protocol experiment and are not enabled by selecting LAN.

## INT-14S Target Write Validation

`v0.2.6-beta.11` added one disabled-by-default diagnostic number per physical probe: `Validate LAN Write: Probe N Food High Target`. A community hardware test confirmed that Probe 1 accepted a 90 C target and showed the high-target indication on the station.

Stable `v0.2.6` includes Food Low, Ambient High and Ambient Low beside the existing Food High control for every probe. Target operations are serialized from payload construction through history recording, and raw zero fields remain unavailable while their threshold mode is disabled instead of appearing as `-17.8 C`. The validation is available only with complete INT-14S Tuya LAN configuration and never falls back to BLE. Each accepted command preserves the other thresholds in the same compound block. Diagnostics report `confirmed_by_readback` only if the station returns the DP and the decoded target matches; otherwise they report `awaiting_visual_confirmation`.

For one compact test, use an idle Probe 1 and enable only its four validation controls. Set Food High to 90 C, Food Low to 10 C, Ambient High to 40 C and Ambient Low to 5 C, in that order. Wait a few seconds after each value and note what the station displays. Download one integration diagnostics file after the fourth write; its bounded history contains all four attempts. Smart Life does not expose Inkbird's cooking controls, so the station display is the useful visual check.

Normal target controls, pre-alarm writes and all other INT-14S settings remain disabled. The diagnostic controls are not the finished settings UI.
