"""Switch platform for BlueStream integration."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BluStreamCoordinator
from .data import BluStreamConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass` pylint: disable=unused-argument
    entry: BluStreamConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BluStream switch platform from a config entry."""
    entities: list[SwitchEntity] = []

    # Add power switch
    entities.append(PowerSwitch(entry.runtime_data.coordinator, entry))

    # Add output switches
    outputs = getattr(entry.runtime_data.coordinator.data, "outputs", [])
    for output in outputs:
        entities.append(OutputSwitch(entry.runtime_data.coordinator, output, entry))

    async_add_entities(entities)

class PowerSwitch(CoordinatorEntity[BluStreamCoordinator], SwitchEntity): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
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

class OutputSwitch(CoordinatorEntity, SwitchEntity): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Switch to control output enabled status."""

    _attr_icon = "mdi:video-check"

    def __init__(
        self, coordinator: BluStreamCoordinator, output: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the output switch."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._output_id = getattr(output, "output_port", -1)
        self._status = getattr(output, "status", None)
        self._entry = entry

        output_port = getattr(output, "output_port", "unknown")
        output_name = getattr(output, "name", f"Output {output_port}").replace("_", " ")

        self._attr_name = f"{output_name} Enabled"
        self._attr_unique_id = f"{DOMAIN}_output_{output_port}_enabled"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
        } # pyright: ignore[reportAttributeAccessIssue]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        outputs = getattr(self._coordinator.data,"outputs",[])
        this_output = next((o for o in outputs if getattr(o, "output_port", -1) == self._output_id), None)
        if this_output is not None:
            self._status = getattr(this_output, "status", None)
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return true if output is enabled."""
        return self._status

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable output."""
        await self._coordinator.config_entry.runtime_data.client.set_output_status(self._output_id, True)
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable output."""
        await self._coordinator.config_entry.runtime_data.client.set_output_status(self._output_id, False)
        await self._coordinator.async_request_refresh()
