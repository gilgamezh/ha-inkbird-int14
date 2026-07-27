# INT-14S-BW Read-Only LAN Diagnostics

INT-14S-BW uses a different Tuya temperature payload layout from INT-14-BW. A successful LAN connection does not make the INT-14-BW decoder compatible with it.

If an INT-14S is configured with the INT-14-BW profile, Home Assistant may show values such as 800 C, negative hundreds of degrees or a base temperature in the thousands. It may also create only two temperature channels per probe instead of the expected five. Those values are parser mismatch artifacts. They are not real readings and must not be corrected with calibration.

## Safe Test Procedure

This diagnostic is available in the `v0.2.6-beta.6` prerelease:

1. Install the prerelease through HACS and restart Home Assistant.
2. Select the correct `INT-14S-BW` model profile.
3. Enter the station host/IP, device ID, local key and protocol version in the integration options.
4. Keep normal transport on `BLE only` or `Auto`. INT-14S normal LAN remains disabled either way.
5. Wake the station and press **Capture Read-Only LAN Diagnostics** once.
6. Wait about 15 seconds.
7. Download the integration diagnostics from Home Assistant.
8. Inspect the file before sharing it, then attach the sanitized JSON to the existing INT-14S validation Discussion.

Discussion:

<https://github.com/zampix1/ha-inkbird-int14/discussions/2>

## What It Sends

The capture performs the same class of local Tuya state queries used for polling:

- one status request;
- one requested-DP refresh.

It does not call the setting-write functions, does not apply the returned values to Home Assistant entities and does not turn on the unsupported INT-14S LAN runtime.

## What It Records

The diagnostics include:

- whether each read query succeeded;
- returned DP numbers;
- numeric and boolean DP values;
- recognized encoded thermometer payloads as hexadecimal;
- type, length and SHA-256 metadata instead of arbitrary strings or unknown binary content.

The capture does not include the configured host, device ID or local key. Home Assistant diagnostics also apply the integration's normal identifier and credential redaction. You should still inspect the file before posting it publicly.

## Current Boundary

This tool is for protocol mapping, not normal operation. INT-14S remains supported through read-only BLE until its Tuya DP meanings, scales, sentinels and state fields have been validated from controlled captures. LAN writes remain blocked.
