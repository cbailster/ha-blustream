"""Config flow for the BluStream integration."""

# from __future__ import annotations

from typing import Any, Self

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.network import is_host_valid

from .const import DOMAIN, LOGGER
from .hdmi_matrix.client import HDMIMatrixClient
from .hdmi_matrix.exceptions import (
    MatrixCommandError,
    MatrixConnectionError,
    MatrixTimeoutError,
)

# Polling interval constraints
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 60
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PORT = 80

# Ask for host and optional port (default 80) and optional scan interval
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int
    }
)


async def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    host: str = data[CONF_HOST]
    port: int = int(data.get(CONF_PORT, DEFAULT_PORT))
    scan_interval: int = int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    # Validate scan interval first if provided
    if scan_interval < MIN_SCAN_INTERVAL or scan_interval > MAX_SCAN_INTERVAL:
        raise InvalidScanInterval

    # Validate host - must be a valid IP address or hostname
    if not is_host_valid(host):
        raise InvalidHost

    # Try to create client and fetch device info
    client = HDMIMatrixClient(host, http_port=port)

    try:
        await client.get_device_info()
    except (MatrixConnectionError, MatrixTimeoutError) as err:
        raise CannotConnect from err
    except MatrixCommandError as err:
        raise InvalidResponse from err

    # Return a title for the config entry (use host)
    return {"title": host}


class HDMIMatrixConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BluStream."""

    VERSION = 1

    host: str | None = None
    port: int | None = None
    scan_interval: int | None = None

    def is_matching(self, other_flow: Self) -> bool: # pyright: ignore[reportIncompatibleMethodOverride]
        """Return True if other_flow is matching this flow."""
        return (
            getattr(other_flow, "host", None) == getattr(self, "host", None)
            and getattr(other_flow, "port", None) == getattr(self, "port", None)
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.host = user_input[CONF_HOST]
            self.port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            self.scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
            try:
                info = await validate_input(user_input)
            except InvalidHost:
                LOGGER.error("Host %s is not a valid IP address or hostname", self.host)
                errors["host"] = "invalid_host"
            except InvalidScanInterval:
                LOGGER.error(
                    "Scan interval %s is out of valid range (%s-%s)",
                    self.scan_interval,
                    MIN_SCAN_INTERVAL,
                    MAX_SCAN_INTERVAL,
                )
                errors["scan_interval"] = "invalid_scan_interval"
            except CannotConnect:
                LOGGER.error("Cannot connect to %s", self.host)
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                LOGGER.error("Device at %s returned an unexpected response", self.host)
                errors["base"] = "invalid_response"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidHost(HomeAssistantError):
    """Error to indicate the provided host is not a valid IP or hostname."""

class InvalidResponse(HomeAssistantError):
    """Error to indicate the device returned an unexpected response."""

class InvalidScanInterval(HomeAssistantError):
    """Error to indicate the polling interval is out of valid range."""
