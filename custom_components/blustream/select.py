"""Select platform for BlueStream integration."""

import asyncio
from typing import Any

from homeassistant.components.select import SelectEntity
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
    """Set up the BluStream select platform from a config entry."""
    entities: list[SelectEntity] = []

    # Add video input selects
    outputs = getattr(entry.runtime_data.coordinator.data, "outputs", [])
    for output in outputs:
        entities.append(VideoInputSelect(entry.runtime_data.coordinator, output, entry))
        entities.append(AudioInputSelect(entry.runtime_data.coordinator, output, entry))

    async_add_entities(entities)

class InputSelect(CoordinatorEntity[BluStreamCoordinator], SelectEntity): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Base class for input select entities."""

    _type: str = ""  # "input" or "audio_input"

    def __init__(
        self, coordinator: BluStreamCoordinator, output: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the input select entity."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._output_id = getattr(output, "output_port", -1)
        self._select = getattr(output, f"{self._type}_port", -1)
        self._entry = entry

        output_port = getattr(output, "output_port", "unknown")
        output_name = getattr(output, "name", f"Output {output_port}").replace("_", " ")

        self._attr_name = f"Select for {output_name}"
        self._attr_unique_id = f"{DOMAIN}_output_{output_port}_{self._type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
        } # pyright: ignore[reportAttributeAccessIssue]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        outputs = getattr(self._coordinator.data,"outputs",[])
        this_output = next((o for o in outputs if getattr(o, "output_port", -1) == self._output_id), None)
        if this_output is not None:
            self._select = getattr(this_output, f"{self._type}_port", -1)
        self.async_write_ha_state()

    @property
    def options(self) -> list[str] | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return a set of selectable options."""
        input_names = self.input_names
        return list(input_names.values()) if input_names else None

    @property
    def current_option(self) -> str | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the name of the currently selected input."""
        input_names = self.input_names
        return input_names.get(self._select) if input_names else None

    @property
    def input_names(self) -> dict[Any, str] | None:
        """Return a dictionary of input names."""
        return getattr(self._coordinator.data, "input_names" if self._type == "input" else "audio_input_options", {})

    def _get_input_id(self, option: str) -> Any | None:
        """Get the input ID for the provided option."""
        input_names = self.input_names
        return next((k for k, v in input_names.items() if v == option), None) if input_names else None

class VideoInputSelect(InputSelect): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Select entity to choose input source for an output."""

    _attr_icon = "mdi:video-input-hdmi"
    _type = "input"

    def __init__(
        self, coordinator: BluStreamCoordinator, output: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the input select entity."""
        super().__init__(coordinator, output, entry)
        self._attr_name = f"Video {self._attr_name}"

    async def async_select_option(self, option: str) -> None:
        """Change the selected input."""
        input_id = self._get_input_id(option)
        if input_id is not None:
            await self._coordinator.config_entry.runtime_data.client.set_input(self._output_id, input_id)
            await asyncio.sleep(5)
            await self._coordinator.async_request_refresh()

class AudioInputSelect(InputSelect): # pyright: ignore[reportIncompatibleVariableOverride] pylint: disable=abstract-method
    """Select entity to choose input source for an output."""

    _attr_icon = "mdi:audio-input-stereo-minijack"
    _type = "audio_input"

    def __init__(
        self, coordinator: BluStreamCoordinator, output: Any, entry: ConfigEntry
    ) -> None:
        """Initialize the input select entity."""
        super().__init__(coordinator, output, entry)

        self._attr_name = f"Audio {self._attr_name}"

    async def async_select_option(self, option: str) -> None:
        """Change the selected input."""
        input_id = self._get_input_id(option)
        if input_id is not None:
            await self._coordinator.config_entry.runtime_data.client.set_audio_input(self._output_id, input_id)
            await asyncio.sleep(5)
            await self._coordinator.async_request_refresh()
