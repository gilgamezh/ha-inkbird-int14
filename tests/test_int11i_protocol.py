from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_protocol_module():
    path = ROOT / "custom_components" / "inkbird_int14" / "protocol.py"
    spec = importlib.util.spec_from_file_location("inkbird_int14_protocol", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_int11i_ff01_temperature_uses_fahrenheit_hundredths() -> None:
    protocol = _load_protocol_module()
    raw = int(7250).to_bytes(2, "little")

    parsed = protocol.parse_int11i_temperature_payload(raw)

    assert parsed["base_temp_f_tenths"] is None
    assert parsed["probes"] == [
        {
            "probe": 1,
            "internal_f_tenths": 725,
            "ambient_f_tenths": None,
        }
    ]


def test_int11i_2a19_battery_uses_base_then_probe() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int11i_battery_payload(bytes([88, 77]))

    assert parsed == {
        "base_power": 88,
        "probe_battery": {1: 77},
    }


def test_int11i_2a19_battery_handles_unknown_marker() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int11i_battery_payload(bytes([0x7F, 0x7F]))

    assert parsed == {
        "base_power": None,
        "probe_battery": {1: None},
    }


def test_int14s_multisensor_ff01_sentinels_are_unavailable() -> None:
    protocol = _load_protocol_module()
    sentinel_block = bytes.fromhex("fe7ffe7ffe7ffe7ffe7ffe7f7e")
    raw = sentinel_block * 4 + bytes.fromhex("4c03")

    parsed = protocol.parse_multisensor_temperature_payload(raw, 4)

    assert parsed["probe_block_length"] == 13
    assert parsed["temperature_slots_per_probe"] == 6
    assert parsed["mapped_temperature_channels_per_probe"] == 5
    assert parsed["base_temp_f_tenths"] == 844
    assert len(parsed["probes"]) == 4
    assert parsed["probes"][0] == {
        "probe": 1,
        "raw_values": [32766] * 6,
        "internal_f_hundredths": None,
        "internal_f_tenths": None,
        "food_f_hundredths": [None] * 4,
        "food_f_tenths": [None] * 4,
        "ambient_f_tenths": None,
        "status": 0x7E,
    }


def test_int14s_multisensor_ff01_uses_confirmed_field_order_and_scales() -> None:
    protocol = _load_protocol_module()
    active_probe = bytes.fromhex("da20f720da20ee2001214a031f")
    sentinel_probe = bytes.fromhex("fe7ffe7ffe7ffe7ffe7ffe7f7e")
    raw = active_probe + sentinel_probe * 3 + bytes.fromhex("4003")

    parsed = protocol.parse_multisensor_temperature_payload(raw, 4)

    assert parsed["base_temp_f_tenths"] == 832
    assert parsed["probes"][0] == {
        "probe": 1,
        "raw_values": [8410, 8439, 8410, 8430, 8449, 842],
        "internal_f_hundredths": 8410,
        "internal_f_tenths": 841,
        "food_f_hundredths": [8439, 8410, 8430, 8449],
        "food_f_tenths": [844, 841, 843, 845],
        "ambient_f_tenths": 842,
        "status": 0x1F,
    }
    assert all(probe["food_f_tenths"] == [None] * 4 for probe in parsed["probes"][1:])


def test_int14s_multisensor_ff01_preserves_negative_temperatures() -> None:
    protocol = _load_protocol_module()
    values = [-125, -124, -123, -122, -121, -120]
    active_probe = b"".join(value.to_bytes(2, "little", signed=True) for value in values) + bytes([0x1F])
    sentinel_probe = bytes.fromhex("fe7ffe7ffe7ffe7ffe7ffe7f7e")
    raw = active_probe + sentinel_probe * 3 + (-119).to_bytes(2, "little", signed=True)

    parsed = protocol.parse_multisensor_temperature_payload(raw, 4)

    assert parsed["probes"][0]["internal_f_tenths"] == -13
    assert parsed["probes"][0]["food_f_tenths"] == [-12, -12, -12, -12]
    assert parsed["probes"][0]["ambient_f_tenths"] == -120
    assert parsed["base_temp_f_tenths"] == -119


def test_multisensor_ff01_rejects_unexpected_length() -> None:
    protocol = _load_protocol_module()

    assert protocol.parse_multisensor_temperature_payload(bytes(18), 4) is None


def test_int14s_lan_dp109_matches_validated_ble_layout_and_crc() -> None:
    protocol = _load_protocol_module()
    raw_hex = "b71efc1eb71ed51ed51f11031cfe7ffe7ffe7ffe7ffe7ffe7f7efe7ffe7ffe7ffe7ffe7ffe7f7efe7ffe7ffe7ffe7ffe7ffe7f7e2003c7"

    parsed = protocol.parse_int14s_lan_dps({"109": raw_hex})

    assert parsed["int14s_lan_payload_length"] == 55
    assert parsed["int14s_lan_crc8_received"] == 0xC7
    assert parsed["int14s_lan_crc8_calculated"] == 0xC7
    assert parsed["int14s_lan_crc8_valid"] is True
    assert parsed["int14s_lan_parse_error"] is None
    assert len(parsed["frames"]) == 1
    frame = parsed["frames"][0]
    assert frame["name"] == "multisensor_current_temp_candidate"
    assert frame["transport"] == "lan_dp109_int14s"
    assert frame["base_temp_f_tenths"] == 800
    assert frame["probes"][0]["internal_f_tenths"] == 786
    assert frame["probes"][0]["food_f_tenths"] == [793, 786, 789, 815]
    assert frame["probes"][0]["ambient_f_tenths"] == 785
    assert frame["probes"][0]["status"] == 0x1C
    assert all(probe["food_f_tenths"] == [None] * 4 for probe in frame["probes"][1:])


def test_int14s_lan_dp109_rejects_bad_crc_without_live_frame() -> None:
    protocol = _load_protocol_module()
    raw = bytearray.fromhex(
        "b71efc1eb71ed51ed51f11031cfe7ffe7ffe7ffe7ffe7ffe7f7efe7ffe7ffe7ffe7ffe7ffe7f7efe7ffe7ffe7ffe7ffe7ffe7f7e2003c7"
    )
    raw[-1] ^= 0x01

    parsed = protocol.parse_int14s_lan_dps({"109": raw.hex()})

    assert parsed["int14s_lan_crc8_valid"] is False
    assert parsed["int14s_lan_parse_error"] == "crc_mismatch"
    assert parsed["frames"] == []


def test_int14s_lan_dp103_decodes_station_and_probe_batteries_with_crc() -> None:
    protocol = _load_protocol_module()
    payload = bytes([82, 75, 64, 53, 42])
    raw = payload + bytes([protocol.crc8_atm(payload)])

    parsed = protocol.parse_int14s_lan_dps({"103": raw.hex()})

    assert parsed["int14s_lan_battery_payload_length"] == 6
    assert parsed["int14s_lan_battery_crc8_received"] == raw[-1]
    assert parsed["int14s_lan_battery_crc8_calculated"] == raw[-1]
    assert parsed["int14s_lan_battery_crc8_valid"] is True
    assert parsed["int14s_lan_battery_parse_error"] is None
    assert parsed["frames"] == [
        {
            "name": "battery_candidate",
            "transport": "lan_dp103_int14s",
            "raw_hex": raw.hex(),
            "base_power": 82,
            "probe_battery": {1: 75, 2: 64, 3: 53, 4: 42},
        }
    ]


def test_int14s_lan_dp103_rejects_bad_crc_without_battery_frame() -> None:
    protocol = _load_protocol_module()
    raw = bytearray.fromhex("6464646464da")
    raw[-1] ^= 0x01

    parsed = protocol.parse_int14s_lan_dps({"103": raw.hex()})

    assert parsed["int14s_lan_battery_crc8_valid"] is False
    assert parsed["int14s_lan_battery_parse_error"] == "crc_mismatch"
    assert parsed["frames"] == []


def test_int14s_lan_dp104_decodes_validated_display_brightness() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int14s_lan_dps({"104": 85})

    assert parsed["frames"] == [
        {
            "name": "display_light_candidate",
            "transport": "lan_dp104_int14s",
            "display_light": 85,
        }
    ]


def test_int14s_lan_dp104_rejects_bool_and_out_of_range_values() -> None:
    protocol = _load_protocol_module()

    for value in (True, 0, 101, "85"):
        assert protocol.parse_int14s_lan_dps({"104": value})["frames"] == []


def test_int14s_lan_target_builder_matches_vendor_20_byte_layout() -> None:
    protocol = _load_protocol_module()

    value = protocol.build_int14s_lan_target_dp_value(
        food_mode="10",
        food_high_f_tenths=1580,
        start_epoch_s=0x12345678,
    )

    assert value == "102c060000000078563412000000000000000000"
    assert len(bytes.fromhex(value)) == 20


def test_int14s_target_modes_preserve_the_other_threshold() -> None:
    protocol = _load_protocol_module()

    assert protocol.target_mode_after_threshold_write("off", "high") == "10"
    assert protocol.target_mode_after_threshold_write("10", "low") == "11"
    assert protocol.target_mode_after_threshold_write("low", "high") == "11"
    assert protocol.target_mode_after_threshold_write("11", "low") == "11"
    assert protocol.normalize_target_mode("high") == "10"
    assert protocol.normalize_target_mode("unexpected") == "00"


def test_int14s_target_mode_rejects_unknown_threshold() -> None:
    protocol = _load_protocol_module()

    try:
        protocol.target_mode_after_threshold_write("off", "middle")
    except ValueError:
        return
    raise AssertionError("expected ValueError for an unknown target threshold")


def test_int14s_compound_target_keeps_all_four_thresholds() -> None:
    protocol = _load_protocol_module()
    payload = bytes.fromhex(
        protocol.build_int14s_lan_target_dp_value(
            food_mode="11",
            food_high_f_tenths=1940,
            food_low_f_tenths=500,
            start_epoch_s=1,
            ambient_mode="11",
            ambient_high_f_tenths=1040,
            ambient_low_f_tenths=410,
        )
    )
    parsed = protocol.parse_int14s_lan_target_dp_value((payload + bytes([protocol.crc8_atm(payload)])).hex(), 1)

    assert parsed is not None
    assert parsed["mode_name"] == "range"
    assert parsed["ambient_mode"] == "11"
    assert parsed["target_high_f_tenths"] == 1940
    assert parsed["target_low_f_tenths"] == 500
    assert parsed["ambient_target_high_f_tenths"] == 1040
    assert parsed["ambient_target_low_f_tenths"] == 410


def test_int14s_lan_dp122_parses_crc_protected_target() -> None:
    protocol = _load_protocol_module()
    payload = bytes.fromhex(
        protocol.build_int14s_lan_target_dp_value(
            food_mode="11",
            food_high_f_tenths=1580,
            food_low_f_tenths=1400,
            start_epoch_s=0x12345678,
            ambient_mode="11",
            ambient_high_f_tenths=750,
            ambient_low_f_tenths=650,
            advance_value=18,
        )
    )
    value = (payload + bytes([protocol.crc8_atm(payload)])).hex()

    parsed = protocol.parse_int14s_lan_dps({"122": value})

    assert parsed["frames"] == [
        {
            "name": "target_candidate",
            "transport": "lan_dp122_int14s",
            "probe": 1,
            "mode": "11",
            "mode_name": "range",
            "target_high_f_tenths": 1580,
            "target_low_f_tenths": 1400,
            "degree_code": "00",
            "food_index": -1,
            "start_epoch_s": 0x12345678,
            "ambient_mode": "11",
            "ambient_target_high_f_tenths": 750,
            "ambient_target_low_f_tenths": 650,
            "ambient_degree_code": "00",
            "ambient_food_index": -1,
            "advance_value": 18,
            "reserved": 0,
            "crc8_received": protocol.crc8_atm(payload),
        }
    ]


def test_int14s_lan_target_rejects_missing_or_bad_crc() -> None:
    protocol = _load_protocol_module()
    payload = bytes.fromhex(protocol.build_int14s_lan_target_dp_value(food_high_f_tenths=1580, start_epoch_s=1))

    assert protocol.parse_int14s_lan_target_dp_value(payload.hex(), 1) is None
    assert protocol.parse_int14s_lan_target_dp_value((payload + b"\x00").hex(), 1) is None


def test_int14s_lan_parser_ignores_unvalidated_dps() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int14s_lan_dps({"101": "C", "102": True, "106": 2})

    assert parsed["dp_keys"] == ["101", "102", "106"]
    assert parsed["frames"] == []
    assert parsed["int14s_lan_parse_error"] is None
    assert parsed["int14s_lan_battery_parse_error"] is None


def test_int12e_capture_decodes_two_multisensor_probe_blocks() -> None:
    protocol = _load_protocol_module()
    raw = bytes.fromhex("3f1da71d3f1d811d021edf0219311d921d311d6d1d441ee5021aee02")

    parsed = protocol.parse_multisensor_temperature_payload(raw, 2)

    assert parsed["base_temp_f_tenths"] == 750
    assert parsed["probes"][0]["food_f_tenths"] == [759, 749, 755, 768]
    assert parsed["probes"][0]["ambient_f_tenths"] == 735
    assert parsed["probes"][0]["status"] == 0x19
    assert parsed["probes"][1]["food_f_tenths"] == [757, 747, 753, 775]
    assert parsed["probes"][1]["ambient_f_tenths"] == 741
    assert parsed["probes"][1]["status"] == 0x1A


def test_int12e_capture_decodes_station_and_two_probe_batteries() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_battery_payload(bytes.fromhex("526464"), probe_count=2)

    assert parsed == {"base_power": 82, "probe_battery": {1: 100, 2: 100}}


def test_diagnostic_snapshot_queries_exclude_clock_sync_and_settings() -> None:
    protocol = _load_protocol_module()

    commands = protocol.split_frames(b"".join(protocol.diagnostic_snapshot_query_chunks()))

    assert [command.hex() for command in commands] == [frame[2:] for frame in protocol.INIT_STATIC_FRAMES]
    assert all(command[0] != 0x19 for command in commands)


def test_unit_write_validation_frames_are_exact_and_station_wide() -> None:
    protocol = _load_protocol_module()

    assert protocol.build_unit_command("C") == bytes.fromhex("020343")
    assert protocol.build_unit_command("F") == bytes.fromhex("020346")
