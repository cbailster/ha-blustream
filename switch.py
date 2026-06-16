"""Switch platform for BlueStream integration."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import BluStreamCoordinator
from .data import BluStreamConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: BluStreamConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[SwitchEntity] = []

    # Add power switch
    entities.append(PowerSwitch(entry.runtime_data.coordinator, entry))

    async_add_entities(entities)

class PowerSwitch(CoordinatorEntity[BluStreamCoordinator], SwitchEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Switch to control power status of the HDMI matrix."""

    _attr_name = "Power"
    _attr_icon = "mdi:power"
    _attr_unique_id = f"{DOMAIN}_power"

    def __init__(self, coordinator: BluStreamCoordinator, entry: ConfigEntry) -> None:
        """Initialize the power switch."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
        } # pyright: ignore[reportAttributeAccessIssue]

    @property
    def is_on(self) -> bool | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return true if power is on."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, "power", None)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on power."""
        await self._coordinator.config_entry.runtime_data.client.set_power(True)
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off power."""
        await self._coordinator.config_entry.runtime_data.client.set_power(False)
        await self._coordinator.async_request_refresh()    