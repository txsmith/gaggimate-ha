"""GaggiMate mode select entity."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODE_BY_NAME, MODE_NAMES, MODES
from .coordinator import GaggiMateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GaggiMate select entities."""
    coordinator: GaggiMateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        GaggiMateModeSelect(coordinator),
        GaggiMateProfileSelect(coordinator),
    ])


class GaggiMateModeSelect(SelectEntity):
    """Select entity to get and set the machine operating mode."""

    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_options = MODES
    _attr_icon = "mdi:coffee-maker"

    def __init__(self, coordinator: GaggiMateCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.host}_mode"
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
    def current_option(self) -> str | None:
        mode_int = self._coordinator.data.get("m")
        if mode_int is None:
            return None
        return MODE_NAMES.get(mode_int)

    async def async_select_option(self, option: str) -> None:
        mode_int = MODE_BY_NAME.get(option)
        if mode_int is not None:
            await self._coordinator.async_set_mode(mode_int)

    async def async_added_to_hass(self) -> None:
        self._unsub = self._coordinator.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class GaggiMateProfileSelect(SelectEntity):
    """Select entity to get and set the active brew profile."""

    _attr_has_entity_name = True
    _attr_name = "Profile"
    _attr_icon = "mdi:coffee"

    def __init__(self, coordinator: GaggiMateCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.host}_profile"
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
    def options(self) -> list[str]:
        return [p["label"] for p in self._coordinator.profiles]

    @property
    def current_option(self) -> str | None:
        return self._coordinator.data.get("p")

    async def async_select_option(self, option: str) -> None:
        for p in self._coordinator.profiles:
            if p["label"] == option:
                await self._coordinator.async_select_profile(p["id"])
                return

    async def async_added_to_hass(self) -> None:
        self._unsub = self._coordinator.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
