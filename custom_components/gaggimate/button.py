"""GaggiMate flush button entity."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GaggiMateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GaggiMate flush button."""
    coordinator: GaggiMateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GaggiMateFlushButton(coordinator)])


class GaggiMateFlushButton(ButtonEntity):
    """Button entity to trigger a flush cycle."""

    _attr_has_entity_name = True
    _attr_name = "Flush"
    _attr_icon = "mdi:water"

    def __init__(self, coordinator: GaggiMateCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.host}_flush"

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

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._coordinator.async_flush()
