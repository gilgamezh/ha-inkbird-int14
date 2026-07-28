from __future__ import annotations

from typing import Protocol

MAX_KNOWN_PHYSICAL_PROBES = 4
INT14S_PROFILE_KEY = "int14s_bw"

KNOWN_TEMPERATURE_ENTITY_KEYS = {
    "internal",
    "ambient",
    "food_1",
    "food_2",
    "food_3",
    "food_4",
}
PROBE_PROTOCOL_STATE_KEYS = {
    "connect",
    "charging",
    "paired",
    "pair_request",
    "internal_low_alarm",
    "internal_high_alarm",
    "internal_over_high_alarm",
    "internal_over_low_alarm",
    "advance_alarm",
    "ambient_over_high_alarm",
    "ambient_over_low_alarm",
    "battery_alarm",
    "battery_report_suspect",
    "timer_alarm",
    "timer_switch",
}
DERIVED_PROBE_STATE_KEYS = {"battery_report_suspect"}
BASE_PROTOCOL_STATE_KEYS = {
    "ble_enabled",
    "ble_connected",
    "cloud_enabled",
    "cloud_available",
    "battery_data_stale",
    "battery_report_suspect",
    "base_battery_report_suspect",
    "probe_battery_report_suspect",
    "sound_enabled",
    "dev_mute",
    "base_charging",
    "wifi_switch",
    "wifi_state",
    "verify",
    "device_over_high_temp_alarm",
    "device_over_low_temp_alarm",
}
DERIVED_BASE_STATE_KEYS = {
    "ble_enabled",
    "ble_connected",
    "cloud_enabled",
    "cloud_available",
    "battery_data_stale",
    "battery_report_suspect",
    "base_battery_report_suspect",
    "probe_battery_report_suspect",
}
PROBE_WRITE_SENSOR_KEYS = {
    "target_high_temp",
    "target_low_temp",
    "target_mode",
    "target_food_index",
    "target_degree_code",
    "advance_value",
    "timer_cd_mode",
    "timer_start_epoch_s",
    "timer_end_epoch_s",
}
PROFILE_BUTTON_KEYS = {
    "request_snapshot",
    "capture_ble_diagnostics",
    "capture_authenticated_ble_diagnostics",
    "capture_read_only_lan_diagnostics",
    "validate_ble_unit_write_c",
    "validate_ble_unit_write_f",
}


class TemperatureChannelLike(Protocol):
    @property
    def data_key(self) -> str: ...

    @property
    def live_entity_key(self) -> str: ...


class ProbeLayoutLike(Protocol):
    index: int

    @property
    def live_temperature_channels(self) -> tuple[TemperatureChannelLike, ...]: ...


class ModelProfileLike(Protocol):
    key: str
    probe_layout: tuple[ProbeLayoutLike, ...]
    write_support: str
    supports_protocol_state: bool
    supports_base_temperature: bool
    supports_ble_snapshot: bool
    supports_ble_diagnostics: bool
    supports_authenticated_ble_diagnostics: bool

    @property
    def physical_probe_count(self) -> int: ...

    @property
    def has_live_runtime_data(self) -> bool: ...


def _known_profile_unique_ids(address: str, max_probe_count: int) -> set[str]:
    unique_ids = {
        f"{address}_base_temp",
        f"{address}_base_battery",
        f"{address}_display_light_command",
        f"{address}_transport_mode",
    }
    unique_ids.update(f"{address}_{key}" for key in BASE_PROTOCOL_STATE_KEYS)
    unique_ids.update(f"{address}_{key}" for key in PROFILE_BUTTON_KEYS)

    for probe in range(1, max_probe_count + 1):
        prefix = f"{address}_probe_{probe}"
        unique_ids.add(f"{prefix}_battery")
        unique_ids.update(f"{prefix}_{key}_temp" for key in KNOWN_TEMPERATURE_ENTITY_KEYS)
        unique_ids.update(f"{prefix}_{key}" for key in PROBE_PROTOCOL_STATE_KEYS)
        unique_ids.update(f"{prefix}_{key}" for key in PROBE_WRITE_SENSOR_KEYS)
        unique_ids.add(f"{prefix}_target_high_command")
        unique_ids.add(f"{prefix}_advance_command")
        for channel in KNOWN_TEMPERATURE_ENTITY_KEYS:
            unique_ids.add(f"{prefix}_{channel}_calibration")
            unique_ids.add(f"{prefix}_{channel}_calibration_command")
    return unique_ids


def expected_profile_unique_ids(address: str, profile: ModelProfileLike) -> set[str]:
    """Return profile-dependent IDs that the current setup is expected to create."""
    unique_ids = {f"{address}_transport_mode"}
    unique_ids.update(f"{address}_{key}" for key in DERIVED_BASE_STATE_KEYS)

    if profile.supports_protocol_state:
        unique_ids.update(f"{address}_{key}" for key in BASE_PROTOCOL_STATE_KEYS)

    if profile.supports_ble_snapshot:
        unique_ids.add(f"{address}_request_snapshot")
    if profile.supports_ble_diagnostics:
        unique_ids.add(f"{address}_capture_ble_diagnostics")
    if profile.supports_authenticated_ble_diagnostics:
        unique_ids.add(f"{address}_capture_authenticated_ble_diagnostics")
    if profile.key == INT14S_PROFILE_KEY:
        unique_ids.update(
            {
                f"{address}_capture_read_only_lan_diagnostics",
                f"{address}_validate_ble_unit_write_c",
                f"{address}_validate_ble_unit_write_f",
            }
        )

    if not profile.has_live_runtime_data:
        return unique_ids

    unique_ids.add(f"{address}_base_battery")
    if profile.supports_base_temperature:
        unique_ids.add(f"{address}_base_temp")

    writes_enabled = profile.write_support != "not_supported"
    if writes_enabled:
        unique_ids.add(f"{address}_display_light_command")

    for probe_layout in profile.probe_layout:
        prefix = f"{address}_probe_{probe_layout.index}"
        unique_ids.add(f"{prefix}_battery")
        unique_ids.update(f"{prefix}_{key}" for key in DERIVED_PROBE_STATE_KEYS)
        if profile.supports_protocol_state:
            unique_ids.update(f"{prefix}_{key}" for key in PROBE_PROTOCOL_STATE_KEYS)
        for channel in probe_layout.live_temperature_channels:
            unique_ids.add(f"{prefix}_{channel.live_entity_key}_temp")

        if not writes_enabled:
            continue
        unique_ids.update(f"{prefix}_{key}" for key in PROBE_WRITE_SENSOR_KEYS)
        unique_ids.add(f"{prefix}_target_high_command")
        unique_ids.add(f"{prefix}_advance_command")
        unique_ids.add(f"{prefix}_internal_calibration_command")
        unique_ids.add(f"{prefix}_ambient_calibration_command")
        for channel in probe_layout.live_temperature_channels:
            unique_ids.add(f"{prefix}_{channel.data_key}_calibration")

    return unique_ids


def obsolete_profile_unique_ids(address: str, profile: ModelProfileLike) -> set[str]:
    """Return only known integration IDs that are incompatible with the profile."""
    max_probe_count = max(MAX_KNOWN_PHYSICAL_PROBES, profile.physical_probe_count)
    known = _known_profile_unique_ids(address, max_probe_count)
    expected = expected_profile_unique_ids(address, profile)
    return known - expected
