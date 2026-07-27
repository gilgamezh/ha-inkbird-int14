from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "inkbird_int14"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_lan_module():
    package_name = "inkbird_int14_lan_test"
    package = types.ModuleType(package_name)
    package.__path__ = [str(COMPONENT)]
    sys.modules[package_name] = package
    _load_module(f"{package_name}.const", COMPONENT / "const.py")
    return _load_module(f"{package_name}.lan", COMPONENT / "lan.py")


class _FakeDevice:
    def __init__(self) -> None:
        self.updatedps_calls: list[tuple[list[int], bool]] = []

    def status(self, *, nowait: bool):
        assert nowait is False
        return {
            "dps": {
                "101": 99,
                "109": bytes.fromhex("01020304"),
                "200": "private-unmapped-value",
            }
        }

    def updatedps(self, dp_ids: list[int], *, nowait: bool):
        self.updatedps_calls.append((dp_ids, nowait))
        return {"dps": {"122": -25, "131": True}}


def test_int14s_lan_capture_is_read_only_and_sanitized(monkeypatch) -> None:
    lan = _load_lan_module()
    device = _FakeDevice()
    monkeypatch.setattr(lan, "_device", lambda config: device)
    config = lan.TuyaLanConfig(
        host="192.0.2.10",
        dev_id="private-device-id",
        local_key="private-local-key",
    )

    capture = lan.capture_lan_diagnostics(config)

    assert capture["status"] == "complete"
    assert capture["read_only"] is True
    assert capture["status_dps"]["101"] == {"type": "int", "value": 99}
    assert capture["status_dps"]["109"] == {
        "type": "encoded_string",
        "encoding": "hex",
        "length": 4,
        "value_hex": "01020304",
    }
    assert capture["status_dps"]["200"]["type"] == "string"
    assert capture["status_dps"]["200"]["length"] == len("private-unmapped-value")
    assert "value" not in capture["status_dps"]["200"]
    assert capture["update_dps"]["122"] == {"type": "int", "value": -25}
    assert capture["update_dps"]["131"] == {"type": "bool", "value": True}
    assert device.updatedps_calls == [(list(config.update_dps), False)]

    serialized = repr(capture)
    assert config.host not in serialized
    assert config.dev_id not in serialized
    assert config.local_key not in serialized
    assert "private-unmapped-value" not in serialized


def test_unknown_binary_dp_is_hashed_not_exported() -> None:
    lan = _load_lan_module()

    summary = lan._diagnostic_dp_value("999", b"unknown-private-binary")

    assert summary["type"] == "bytes"
    assert summary["length"] == len(b"unknown-private-binary")
    assert "value_hex" not in summary
    assert len(summary["sha256"]) == 64
