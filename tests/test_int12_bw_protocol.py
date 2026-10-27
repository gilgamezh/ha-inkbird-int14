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


def test_int12_bw_ff01_both_probes_idle() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int12_bw_temperature_payload(bytes.fromhex("d200d20018d200180203"))

    assert parsed["base_temp_f_tenths"] == 770
    assert parsed["probes"] == [
        {"probe": 1, "internal_f_tenths": 698, "ambient_f_tenths": 698},
        {"probe": 2, "internal_f_tenths": 698, "ambient_f_tenths": 752, "unmapped_c": 24},
    ]


def test_int12_bw_ff01_probe_1_docked_probe_2_held() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int12_bw_temperature_payload(bytes.fromhex("fe7ffe7f1b180120fb02"))

    assert parsed["base_temp_f_tenths"] == 763
    assert parsed["probes"] == [
        {"probe": 1, "internal_f_tenths": 32766, "ambient_f_tenths": 32766},
        {"probe": 2, "internal_f_tenths": 824, "ambient_f_tenths": 896, "unmapped_c": 27},
    ]


def test_int12_bw_ff01_probe_2_docked_is_unavailable() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_int12_bw_temperature_payload(bytes.fromhex("d200d20018fe7f180203"))

    assert parsed["probes"][1] == {"probe": 2, "internal_f_tenths": 32766, "ambient_f_tenths": 32766, "unmapped_c": None}


def test_int12_bw_ff01_rejects_other_lengths() -> None:
    protocol = _load_protocol_module()

    assert protocol.parse_int12_bw_temperature_payload(bytes(18)) is None
    assert protocol.parse_int12_bw_temperature_payload(bytes(9)) is None


def test_int12_bw_2a19_battery_uses_station_then_two_probes() -> None:
    protocol = _load_protocol_module()

    parsed = protocol.parse_battery_payload(bytes.fromhex("506464"), 2)

    assert parsed == {"base_power": 80, "probe_battery": {1: 100, 2: 100}}
