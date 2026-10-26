# Cook Control Validation

Cook Control for v0.2.10 checked on 2026-10-26 with Home Assistant 2026.10.4 and INT-14-BW.
This page distinguishes observed behaviour from tests using controlled inputs.

## On A Running Home Assistant

| Check | Result |
| --- | --- |
| Four physical probes, eight live food/ambient channels | Populated during a real cook; existing entity, unique and device IDs preserved. |
| Existing cook | Probe 1 name, HA target and station threshold preserved. No thermometer write, pairing change or HA restart. |
| Threshold automation | On unused probe 2, lowered only its HA target below its real room-temperature reading. The real 30-second trigger ran. Echo speech and LG text were both physically confirmed by the owner. Test helpers restored. |
| Rest reminder and snooze | Actual five-minute timers completed and invoked the notification router. Timer traces finished without errors. No claim of separate physical confirmation for each repeated message. |
| Dismiss | Synthetic Companion-action event cancelled both running reminder scripts. |
| Cook change | Changing the test probe's name cancelled its pending snooze. |
| Malformed action | Incomplete `BBQ_` event rejected by conditions, not treated as a probe number. |
| Settings | YAML configuration check passed; no new BBQ errors in the system log. Unrelated automation enablement preserved. |
| Desktop and mobile | Cook and probe views checked at 1600x1200 and 390x844. Two-point probe diagram, no five-channel placeholder. |

The threshold test is a controlled HA-level crossing, not proof that the food in
probe 1 reached its target. It also does not test the station's physical buzzer.
The Companion events were sent to HA for testing; mobile-phone delivery was not
configured or physically checked.

## Automated Coverage

The optional package tests exercise active/disabled probes, stale/future timestamps,
missing or non-numeric temperatures, Celsius conversion, target deduplication,
rest/snooze cancellation, strict action validation, suspect batteries, continuous
stall prerequisites, native Alexa routing and nonintrusive TV behaviour.

Dashboard tests check eight mapped channels, model rejection, first-run discovery,
single-prefix setup, language regeneration, valid button-card styles and the
two-sensor diagram. The ZIP builder uses an explicit file allowlist and reproducible
metadata; it includes no live configuration or captured diagnostics.

## Not Claimed

- No forced physical low-battery, disconnected-probe or fault test in this cook.
  Battery and missing-data guards were tested with fixtures.
- No observed 45-minute real cooking stall. Its conditions and timer structure
  were checked automatically.
- No end-to-end generic TTS provider or mobile push test. Native Alexa and LG
  text are the physical outputs verified here.
- No Tuya LAN test in this cooking session; it used BLE. Both local packet
  timestamps are accepted by the freshness guard.
- No multi-station or multisensor-model dashboard validation.
- A station packet does not independently prove every probe is healthy. Values
  and availability still depend on what the integration can decode.

## Publication Boundary

This is an optional bundle in integration release v0.2.10. Only the manifest
version changes under `custom_components/inkbird_int14`; runtime code is unchanged.
Do not advertise an
automatic HACS dashboard installation: the package requires the documented
configuration copy and resource registration.

Screenshots are framed in the running dashboard to exclude home navigation,
account details and media-device names. Temperatures and user-selected targets
are real displayed values, not recommended cooking temperatures. Graphs show
recorded history; battery values are reports, including the visible suspect flag.
