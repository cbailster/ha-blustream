"""Data coordinator for BlueStream integration."""

from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER
from .data import BluStreamConfigEntry
from .hdmi_matrix.exceptions import (
    MatrixCommandError,
    MatrixConnectionError,
    MatrixTimeoutError,
)

MAX_FAILURES = 3

class BluStreamCoordinator(DataUpdateCoordinator):
    """BluStream data update coordinator."""

    config_entry: BluStreamConfigEntry
    consecutive_failures: int = 0

    async def _async_update_data(self) -> Any:
        """Fetch data from the BluStream device."""
        try:
            LOGGER.debug("Updating BluStream data")
            device_info = await self.config_entry.runtime_data.client.get_device_info()
            self.consecutive_failures = 0  # Reset on successful update
            return device_info
        except (MatrixConnectionError, MatrixTimeoutError) as err:
            self.consecutive_failures += 1
            LOGGER.error("Error connecting to BluStream device: %s, consecutive failures: %s", err, self.consecutive_failures)
            if self.consecutive_failures >= MAX_FAILURES:
                raise UpdateFailed(f"Error connecting to BluStream device: {err}") from err
        except MatrixCommandError as err:
            self.consecutive_failures += 1
            LOGGER.error("Error fetching data from BluStream device: %s, consecutive failures: %s", err, self.consecutive_failures)
            if self.consecutive_failures >= MAX_FAILURES:
                raise UpdateFailed(f"Error fetching data from BluStream device: {err}") from err
