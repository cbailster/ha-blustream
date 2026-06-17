"""Sensor platform for BlueStream integration."""

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
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
    entities: list[BinarySensorEntity] = []


    # Add output switches
    inputs = getattr(entry.runtime_data.coordinator.data, "inputs", [])
    for input_port in inputs:
        entities.append(InputActiveSensor(entry.runtime_data.coordinator, input_port, entry))

    async_add_entities(entities)

class InputActiveSensor(CoordinatorEntity, BinarySensorEntity): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Sensor to display input active status."""

    _attr_icon = "mdi:video-check"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: BluStreamCoordinator, input_data: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the input status sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._input_id = getattr(input_data, "input_port", -1)
        self._entry = entry

        input_name = getattr(input_data, "name", f"Input {self._input_id}").replace("_", " ")

        self._attr_name = f"{input_name} Enabled"
        self._attr_unique_id = f"{DOMAIN}_input_{self._input_id}_enabled"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
        } # pyright: ignore[reportAttributeAccessIssue]

    @property
    def is_on(self) -> bool | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the native value of the sensor."""
        inputs = getattr(self._coordinator.data,"inputs",[])
        this_input = next((o for o in inputs if getattr(o, "input_port", -1) == self._input_id), None)
        if this_input is not None:
            return getattr(this_input, "status", None)
        return None
