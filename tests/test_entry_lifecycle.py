"""Exercise production lifecycle/flow methods with small HA boundary doubles.

AST loading keeps these tests runnable without HA's Linux-only dependencies.
The methods execute unchanged; this is not a full Home Assistant instance test.
"""

from __future__ import annotations

import ast
import asyncio
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "inkbird_int14"


def _load_definitions(filename, names, namespace):
    tree = ast.parse((COMPONENT / filename).read_text(encoding="utf-8"))
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" or getattr(node, "name", None) in names
    ]
    exec(compile(tree, str(COMPONENT / filename), "exec"), namespace)
    return SimpleNamespace(**namespace)


class _FlowBase:
    def __init_subclass__(cls, **kwargs):
        pass

    async def async_set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def _abort_if_unique_id_mismatch(self):
        assert self.unique_id == self.entry.unique_id

    def _get_reconfigure_entry(self):
        return self.entry

    def async_abort(self, *, reason):
        return {"type": "abort", "reason": reason}


class _OptionsBase:
    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_known_entry(self.handler)


def _flows():
    namespace = runpy.run_path(str(COMPONENT / "const.py"))
    namespace.update(
        config_entries=SimpleNamespace(ConfigFlow=_FlowBase, OptionsFlow=_OptionsBase),
        DEFAULT_MODEL="int14_bw",
    )
    tree = ast.parse((COMPONENT / "config_flow.py").read_text(encoding="utf-8"))
    keys = next(node for node in tree.body if isinstance(node, ast.Assign) and node.targets[0].id == "RECONFIGURE_OPTION_KEYS")
    exec(compile(ast.Module(body=[keys], type_ignores=[]), "config_flow.py", "exec"), namespace)
    return _load_definitions(
        "config_flow.py",
        {"_stripped", "_entry_data_from_input", "_options_without_reconfigured_keys", "InkbirdInt14ConfigFlow", "InkbirdInt14OptionsFlow"},
        namespace,
    )


def _lifecycle():
    return _load_definitions(
        "__init__.py",
        {"async_unload_entry", "async_reload_entry"},
        {"DOMAIN": "inkbird_int14", "PLATFORMS": ["sensor", "binary_sensor", "button", "select", "number"]},
    )


@pytest.mark.parametrize("loaded", [True, False])
def test_reconfigure_schedules_one_managed_reload_and_preserves_identity(loaded):
    async def scenario():
        lifecycle = _lifecycle()
        flows = _flows()
        submitted = flows._entry_data_from_input({"address": "AA:BB:CC:DD:EE:FF", "model": "int14s_bw", "transport_mode": "BLE only"})
        entry = SimpleNamespace(
            entry_id="test-entry",
            unique_id=submitted["address"],
            title=submitted["name"],
            data={**submitted, "transport_mode": "Auto", "preserved_field": "keep"},
            options={"transport_mode": "Auto", "cloud_history_enabled": False},
            update_listeners=[lifecycle.async_reload_entry] if loaded else [],
        )
        manager = SimpleNamespace(async_schedule_reload=Mock(), async_reload=AsyncMock())
        hass = SimpleNamespace(config_entries=manager)
        listener_tasks = []

        def update(updated_entry, **changes):
            changed = any(getattr(updated_entry, key) != value for key, value in changes.items())
            for key, value in changes.items():
                setattr(updated_entry, key, value)
            if changed:
                for listener in updated_entry.update_listeners:
                    listener_tasks.append(asyncio.create_task(listener(hass, updated_entry)))
            return changed

        manager.async_update_entry = update
        flow = flows.InkbirdInt14ConfigFlow()
        flow.hass = hass
        flow.entry = entry
        flow._async_test_lan_config = AsyncMock()

        result = await flow.async_step_reconfigure(submitted)
        await asyncio.gather(*listener_tasks)

        assert result == {"type": "abort", "reason": "reconfigure_successful"}
        manager.async_schedule_reload.assert_called_once_with("test-entry")
        manager.async_reload.assert_not_awaited()
        assert entry.entry_id == "test-entry"
        assert entry.unique_id == "AA:BB:CC:DD:EE:FF"
        assert entry.data["transport_mode"] == "BLE only"
        assert entry.data["preserved_field"] == "keep"
        assert entry.options == {"cloud_history_enabled": False}

        if loaded:
            manager.async_schedule_reload.reset_mock()
            await flow.async_step_reconfigure(submitted)
            manager.async_schedule_reload.assert_not_called()

    asyncio.run(scenario())


def test_update_listener_delegates_reload_to_home_assistant():
    manager = SimpleNamespace(async_schedule_reload=Mock())
    # No data/platform API: the callback must not unload/setup entries itself.
    asyncio.run(_lifecycle().async_reload_entry(SimpleNamespace(config_entries=manager), SimpleNamespace(entry_id="test-entry")))
    manager.async_schedule_reload.assert_called_once_with("test-entry")


@pytest.mark.parametrize("unload_ok", [True, False])
def test_unload_only_stops_runtime_after_platforms_unload(unload_ok):
    runtime = SimpleNamespace(stop=AsyncMock())
    other_runtime = SimpleNamespace(stop=AsyncMock())
    entries = {"test-entry": runtime, "other-entry": other_runtime}
    manager = SimpleNamespace(async_unload_platforms=AsyncMock(return_value=unload_ok))
    hass = SimpleNamespace(config_entries=manager, data={"inkbird_int14": entries})

    assert asyncio.run(_lifecycle().async_unload_entry(hass, SimpleNamespace(entry_id="test-entry"))) is unload_ok
    if unload_ok:
        runtime.stop.assert_awaited_once()
        assert "test-entry" not in entries
    else:
        runtime.stop.assert_not_awaited()
        assert entries["test-entry"] is runtime
    assert entries["other-entry"] is other_runtime
    other_runtime.stop.assert_not_awaited()


def test_unload_exception_keeps_runtime_for_recovery():
    runtime = SimpleNamespace(stop=AsyncMock())
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_unload_platforms=AsyncMock(side_effect=ValueError("unload failed"))),
        data={"inkbird_int14": {"test-entry": runtime}},
    )
    with pytest.raises(ValueError, match="unload failed"):
        asyncio.run(_lifecycle().async_unload_entry(hass, SimpleNamespace(entry_id="test-entry")))
    runtime.stop.assert_not_awaited()
    assert hass.data["inkbird_int14"]["test-entry"] is runtime


def test_unload_handles_missing_runtime():
    hass = SimpleNamespace(config_entries=SimpleNamespace(async_unload_platforms=AsyncMock(return_value=True)), data={})
    assert asyncio.run(_lifecycle().async_unload_entry(hass, SimpleNamespace(entry_id="test-entry")))


def test_options_flow_uses_framework_read_only_config_entry():
    flows = _flows()
    entry = SimpleNamespace(data={"transport_mode": "Auto"}, options={"transport_mode": "BLE only"})
    flow = flows.InkbirdInt14ConfigFlow.async_get_options_flow(entry)
    flow.hass = SimpleNamespace(config_entries=SimpleNamespace(async_get_known_entry=Mock(return_value=entry)))
    flow.handler = "test-entry"

    assert flow.config_entry is entry
    assert flow._defaults() == {"transport_mode": "BLE only"}
    flow.hass.config_entries.async_get_known_entry.assert_called_with("test-entry")
