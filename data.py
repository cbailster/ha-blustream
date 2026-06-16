"""Common data types for the BluStream integration."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

if TYPE_CHECKING:
    from .coordinator import BluStreamCoordinator
    from .hdmi_matrix import HDMIMatrixClient

type BluStreamConfigEntry = ConfigEntry["BluStreamData"]


@dataclass
class BluStreamData:
    """Data for the BluStream integration."""

    client: "HDMIMatrixClient"
    coordinator: "BluStreamCoordinator"
    integration: Integration