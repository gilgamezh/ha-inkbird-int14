from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, DOMAIN
from .models import MODEL_INT14S_BW
from .protocol import target_mode_has_threshold

DEGREE_CODE_TO_INDEX = {
    "01": 1,
    "03": 2,
    "05": 3,
    "07": 4,
    "0a": 5,
}
DEFAULT_PRE_ALARM_VALUES = (18, 18, 72, 18)
INT14S_TARGET_VALIDATION_FIELDS = (
    ("food_high", "Food High Target", "target_high_f_tenths", "validate_lan_target_high"),
    ("food_low", "Food Low Target", "target_low_f_tenths", "validate_lan_target_low"),
    ("ambient_high", "Ambient High Target", "ambient_target_high_f_tenths", "validate_lan_ambient_target_high"),
    ("ambient_low", "Ambient Low Target", "ambient_target_low_f_tenths", "validate_lan_ambient_target_low"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    base_name = entry.data[CONF_NAME]
    if runtime.profile.key == MODEL_INT14S_BW:
        entities = [
            Int14sTargetValidationNumber(runtime, base_name, probe_layout.index, field, label, data_suffix, unique_suffix)
            for probe_layout in runtime.profile.probe_layout
            for field, label, data_suffix, unique_suffix in INT14S_TARGET_VALIDATION_FIELDS
        ]
        async_add_entities(entities)
        return
    if runtime.profile.write_support == "not_supported" or not runtime.profile.has_live_runtime_data:
        async_add_entities([])
        return
    entities: list[NumberEntity] = [Int14DisplayLightNumber(runtime, base_name)]
    for probe_layout in runtime.profile.probe_layout:
        probe = probe_layout.index
        entities.append(Int14TargetHighNumber(runtime, base_name, probe))
        entities.append(Int14CalibrationNumber(runtime, base_name, probe, "internal"))
        entities.append(Int14CalibrationNumber(runtime, base_name, probe, "ambient"))
        entities.append(Int14PreAlarmNumber(runtime, base_name, probe))
    async_add_entities(entities)


class Int14NumberBase(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(self, runtime, base_name: str) -> None:
        self.runtime = runtime
        self._base_name = base_name
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        self._remove_listener = self.runtime.add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener is not None:
            self._remove_listener()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.runtime.address.upper())},
            "name": self._base_name,
            "manufacturer": "Inkbird",
            "model": self.runtime.device_model,
        }

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class Int14sTargetValidationNumber(Int14NumberBase):
    """Disabled-by-default INT-14S LAN target validation control."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 0
    _attr_native_max_value = 300
    _attr_native_step = 1
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        runtime,
        base_name: str,
        probe: int,
        field: str,
        label: str,
        data_suffix: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(runtime, base_name)
        self.probe = probe
        self.field = field
        self.data_suffix = data_suffix
        self.threshold = "high" if field.endswith("high") else "low"
        self.mode_data_suffix = "ambient_target_mode" if field.startswith("ambient") else "target_mode_code"
        self._attr_unique_id = f"{runtime.address}_probe_{probe}_{unique_suffix}"
        self._attr_name = f"Validate LAN Write: Probe {probe} {label}"

    @property
    def available(self) -> bool:
        return bool(
            self.runtime.lan_enabled
            and self.runtime.lan_config is not None
            and self.runtime.lan_config.is_complete
            and not self.runtime.data.get("target_write_validation_active")
        )

    @property
    def native_value(self):
        mode = self.runtime.data.get(f"probe_{self.probe}_{self.mode_data_suffix}")
        if self.mode_data_suffix == "target_mode_code" and mode is None:
            mode = self.runtime.data.get(f"probe_{self.probe}_target_mode")
        if not target_mode_has_threshold(mode, self.threshold):
            return None
        value = self.runtime.data.get(f"probe_{self.probe}_{self.data_suffix}")
        if value is not None:
            return round((value - 320) / 18, 1)
        if (
            self.runtime.data.get("target_write_validation_probe") == self.probe
            and self.runtime.data.get("target_write_validation_field") == self.field
        ):
            return self.runtime.data.get("target_write_validation_requested_c")
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.request_int14s_target_write_validation(self.probe, self.field, value)


class Int14DisplayLightNumber(Int14NumberBase):
    _attr_name = "Display Light Command"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, runtime, base_name: str) -> None:
        super().__init__(runtime, base_name)
        self._attr_unique_id = f"{runtime.address}_display_light_command"

    @property
    def native_value(self):
        return self.runtime.data.get("display_light")

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.write_display_light(round(value))


class Int14TargetHighNumber(Int14NumberBase):
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_native_min_value = 32
    _attr_native_max_value = 572
    _attr_native_step = 1

    def __init__(self, runtime, base_name: str, probe: int) -> None:
        super().__init__(runtime, base_name)
        self.probe = probe
        self._attr_unique_id = f"{runtime.address}_probe_{probe}_target_high_command"
        self._attr_name = f"Probe {probe} Target High Command"

    @property
    def native_value(self):
        value = self.runtime.data.get(f"probe_{self.probe}_target_high_f_tenths")
        if value in {None, 32766, 32767, 32768}:
            return None
        return value / 10

    async def async_set_native_value(self, value: float) -> None:
        degree_code = self.runtime.data.get(f"probe_{self.probe}_target_degree_code")
        degree_index = DEGREE_CODE_TO_INDEX.get(str(degree_code).lower(), 0)
        food_index = self.runtime.data.get(f"probe_{self.probe}_target_food_index")
        if food_index is None:
            food_index = -1
        await self.runtime.write_target_high(
            probe=self.probe,
            high_tenths=round(value * 10),
            degree_index=degree_index,
            food_index=int(food_index),
        )


class Int14CalibrationNumber(Int14NumberBase):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = -10
    _attr_native_max_value = 10
    _attr_native_step = 0.1
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, runtime, base_name: str, probe: int, channel: str) -> None:
        super().__init__(runtime, base_name)
        self.probe = probe
        self.channel = channel
        self._attr_unique_id = f"{runtime.address}_probe_{probe}_{channel}_calibration_command"
        self._attr_name = f"Probe {probe} {channel.title()} Calibration Command"

    @property
    def native_value(self):
        return self.runtime.data.get(f"probe_{self.probe}_{self.channel}_calibration_c")

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.write_calibration(
            probe=self.probe,
            channel=self.channel,
            c_value=value,
        )


class Int14PreAlarmNumber(Int14NumberBase):
    _attr_name = None
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1

    def __init__(self, runtime, base_name: str, probe: int) -> None:
        super().__init__(runtime, base_name)
        self.probe = probe
        self._attr_unique_id = f"{runtime.address}_probe_{probe}_advance_command"
        self._attr_name = f"Probe {probe} Advance Command"

    @property
    def native_value(self):
        return self.runtime.data.get(f"probe_{self.probe}_advance_value")

    async def async_set_native_value(self, value: float) -> None:
        values = []
        for index in range(1, self.runtime.probe_count + 1):
            current = self.runtime.data.get(f"probe_{index}_advance_value")
            fallback = DEFAULT_PRE_ALARM_VALUES[index - 1]
            values.append(round(value) if index == self.probe else int(current if current is not None else fallback))
        await self.runtime.write_pre_alarm(self.probe, values)
