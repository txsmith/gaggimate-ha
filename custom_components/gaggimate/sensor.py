"""GaggiMate sensor entities - temperature and pressure."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GaggiMateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GaggiMate sensors."""
    coordinator: GaggiMateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        GaggiMateTemperatureSensor(coordinator, "current_temperature", "ct", "Current Temperature"),
        GaggiMateTemperatureSensor(coordinator, "target_temperature", "tt", "Target Temperature"),
        GaggiMatePressureSensor(coordinator),
    ])


class _GaggiMateBaseSensor(SensorEntity):
    """Base class for GaggiMate sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GaggiMateCoordinator,
        key: str,
        data_key: str,
        name: str,
    ) -> None:
        self._coordinator = coordinator
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._unsub = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._coordinator.host)},
            "name": "GaggiMate",
            "manufacturer": "GaggiMate",
            "model": "GaggiMate",
        }

    @property
    def available(self) -> bool:
        return self._coordinator.available

    @property
    def native_value(self):
        return self._coordinator.data.get(self._data_key)

    async def async_added_to_hass(self) -> None:
        self._unsub = self._coordinator.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class GaggiMateTemperatureSensor(_GaggiMateBaseSensor):
    """Current or target boiler temperature."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1


class GaggiMatePressureSensor(_GaggiMateBaseSensor):
    """Current group head pressure."""

    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bar"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: GaggiMateCoordinator) -> None:
        super().__init__(coordinator, "pressure", "pr", "Pressure")
