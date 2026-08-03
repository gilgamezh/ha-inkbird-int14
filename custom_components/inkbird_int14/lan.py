from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_LAN_DEVICE_ID,
    CONF_LAN_HOST,
    CONF_LAN_LOCAL_KEY,
    CONF_LAN_POLL_SECONDS,
    CONF_LAN_PORT,
    CONF_LAN_VERSION,
    DEFAULT_LAN_POLL_SECONDS,
    DEFAULT_LAN_PORT,
    DEFAULT_LAN_VERSION,
)

RAW_DP_IDS = {
    "103",
    "109",
    "110",
    "116",
    "122",
    "123",
    "124",
    "125",
    "126",
    "127",
    "128",
    "129",
    "131",
}
DIAGNOSTIC_DP_IDS = {
    "101",
    "102",
    "103",
    "104",
    "106",
    "109",
    "110",
    "116",
    "122",
    "123",
    "124",
    "125",
    "126",
    "127",
    "128",
    "129",
    "131",
}


@dataclass(frozen=True)
class TuyaLanConfig:
    host: str = ""
    dev_id: str = ""
    local_key: str = ""
    version: float = 3.5
    port: int = 6668
    poll_seconds: int = DEFAULT_LAN_POLL_SECONDS
    timeout: float = 8.0
    status_dps: tuple[int, ...] = (101, 102, 104, 106)
    update_dps: tuple[int, ...] = (103, 109, 110, 116, 122, 123, 124, 125, 126, 127, 128, 129, 131)

    @property
    def is_complete(self) -> bool:
        return bool(self.host and self.dev_id and self.local_key)


def _first_config_value(entry_options: dict[str, Any], entry_data: dict[str, Any], key: str, default: Any = "") -> Any:
    option_value = entry_options.get(key)
    if option_value not in (None, ""):
        return option_value
    data_value = entry_data.get(key)
    if data_value not in (None, ""):
        return data_value
    return default


def build_lan_config_from_sources(entry_data: dict[str, Any], entry_options: dict[str, Any]) -> TuyaLanConfig | None:
    host = str(_first_config_value(entry_options, entry_data, CONF_LAN_HOST)).strip()
    dev_id = str(_first_config_value(entry_options, entry_data, CONF_LAN_DEVICE_ID)).strip()
    local_key = str(_first_config_value(entry_options, entry_data, CONF_LAN_LOCAL_KEY)).strip()
    if not any((host, dev_id, local_key)):
        return None
    return TuyaLanConfig(
        host=host,
        dev_id=dev_id,
        local_key=local_key,
        version=float(_first_config_value(entry_options, entry_data, CONF_LAN_VERSION, DEFAULT_LAN_VERSION)),
        port=int(_first_config_value(entry_options, entry_data, CONF_LAN_PORT, DEFAULT_LAN_PORT)),
        poll_seconds=max(5, int(_first_config_value(entry_options, entry_data, CONF_LAN_POLL_SECONDS, DEFAULT_LAN_POLL_SECONDS))),
    )


def _device(config: TuyaLanConfig):
    import tinytuya

    device = tinytuya.Device(
        config.dev_id,
        config.host,
        config.local_key,
        version=config.version,
        port=config.port,
        connection_timeout=config.timeout,
    )
    device.set_socketTimeout(config.timeout)
    return device


def _normalize_raw_value(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if not isinstance(value, str):
        return value
    text = value.strip()
    if len(text) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", text):
        return text.lower()
    try:
        decoded = base64.b64decode(text, validate=True)
    except Exception:  # noqa: BLE001 - leave original for parser diagnostics
        return value
    return decoded.hex() if decoded else value


def encode_raw_dp_hex(value: str) -> str:
    """Encode a hex payload for a Tuya raw DP carried as Base64 in local JSON."""
    text = value.strip()
    if len(text) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", text):
        raise ValueError("raw DP value must be even-length hex")
    return base64.b64encode(bytes.fromhex(text)).decode("ascii")


def _normalize_dps(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    dps = result.get("dps")
    if not isinstance(dps, dict):
        return {}
    normalized = {str(key): value for key, value in dps.items()}
    for key in list(normalized):
        if key in RAW_DP_IDS:
            normalized[key] = _normalize_raw_value(normalized[key])
    return normalized


def _diagnostic_dp_value(key: str, value: Any) -> dict[str, Any]:
    """Summarize a DP without exposing arbitrary strings or nested payloads."""
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    if value is None:
        return {"type": "none", "value": None}

    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        if key in DIAGNOSTIC_DP_IDS:
            return {
                "type": "bytes",
                "encoding": "hex",
                "length": len(raw),
                "value_hex": raw.hex(),
            }
        return {
            "type": "bytes",
            "length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    if isinstance(value, str):
        raw = value.encode("utf-8", errors="replace")
        normalized = _normalize_raw_value(value) if key in RAW_DP_IDS else value
        if key in DIAGNOSTIC_DP_IDS and isinstance(normalized, str) and len(normalized) % 2 == 0 and re.fullmatch(r"[0-9a-f]+", normalized):
            return {
                "type": "encoded_string",
                "encoding": "hex",
                "length": len(normalized) // 2,
                "value_hex": normalized,
            }
        return {
            "type": "string",
            "length": len(value),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    if isinstance(value, (list, tuple, set, dict)):
        return {"type": type(value).__name__, "item_count": len(value)}
    return {"type": type(value).__name__}


def _diagnostic_dps(result: Any) -> dict[str, dict[str, Any]]:
    dps = _normalize_dps(result)
    return {key: _diagnostic_dp_value(key, value) for key, value in sorted(dps.items())}


def capture_lan_diagnostics(config: TuyaLanConfig) -> dict[str, Any]:
    """Query Tuya LAN state without applying values or sending setting writes."""
    device = _device(config)
    status: Any = None
    update: Any = None
    status_error_type = None
    update_error_type = None

    try:
        status = device.status(nowait=False)
    except Exception as exc:  # noqa: BLE001 - only the exception type is exported
        status_error_type = type(exc).__name__

    if config.update_dps:
        try:
            update = device.updatedps(list(config.update_dps), nowait=False)
        except Exception as exc:  # noqa: BLE001 - only the exception type is exported
            update_error_type = type(exc).__name__

    status_dps = _diagnostic_dps(status)
    update_dps = _diagnostic_dps(update)
    merged_keys = sorted(set(status_dps) | set(update_dps))
    status_ok = isinstance(status, dict) and "Error" not in status and status_error_type is None
    update_ok = isinstance(update, dict) and "Error" not in update and update_error_type is None if config.update_dps else None
    return {
        "status": "complete" if (status_ok or update_ok) else "failed",
        "read_only": True,
        "status_ok": status_ok,
        "update_ok": update_ok,
        "status_error_type": status_error_type,
        "update_error_type": update_error_type,
        "status_dps": status_dps,
        "update_dps": update_dps,
        "dp_count": len(merged_keys),
        "dp_keys": merged_keys,
    }


def fetch_lan_dps(config: TuyaLanConfig) -> tuple[dict[str, Any], dict[str, Any]]:
    device = _device(config)
    dps: dict[str, Any] = {}
    status = device.status(nowait=False)
    dps.update(_normalize_dps(status))

    update = None
    if config.update_dps:
        try:
            update = device.updatedps(list(config.update_dps), nowait=False)
            dps.update(_normalize_dps(update))
        except Exception as exc:  # noqa: BLE001 - surfaced in summary for diagnostics
            update = {"Error": str(exc)}

    summary = {
        "status_ok": isinstance(status, dict) and "Error" not in status,
        "update_ok": isinstance(update, dict) and "Error" not in update if update is not None else None,
        "status_error": status.get("Error") if isinstance(status, dict) else None,
        "status_err": status.get("Err") if isinstance(status, dict) else None,
        "update_error": update.get("Error") if isinstance(update, dict) else None,
        "update_err": update.get("Err") if isinstance(update, dict) else None,
        "dps_count": len(dps),
        "dps_keys": sorted(dps.keys()),
    }
    return dps, summary


def set_lan_dps(config: TuyaLanConfig, dps: dict[str, Any]) -> dict[str, Any]:
    device = _device(config)
    normalized = {str(key): value for key, value in dps.items()}
    if len(normalized) == 1:
        key, value = next(iter(normalized.items()))
        result = device.set_value(key, value, nowait=False)
    else:
        result = device.set_multiple_values(normalized, nowait=False)
    return {
        "ok": isinstance(result, dict) and "Error" not in result,
        "error": result.get("Error") if isinstance(result, dict) else None,
        "err": result.get("Err") if isinstance(result, dict) else None,
        "result_type": type(result).__name__,
    }
