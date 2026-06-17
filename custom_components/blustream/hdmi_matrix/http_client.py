"""HTTP client for communicating with HDMI matrix devices."""

import asyncio
from typing import Any

import aiohttp

from .exceptions import MatrixCommandError, MatrixConnectionError, MatrixTimeoutError


class HTTPClient:
    """HTTP client for communicating with HDMI matrix over HTTP protocol.

    Attributes:
        host: IP address or hostname of the matrix device
        port: HTTP port number (default: 80)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        host: str,
        port: int = 80,
        timeout: int = 10,
    ) -> None:
        """Initialize HTTP client.

        Args:
            host: IP address or hostname of the matrix device
            port: HTTP port number (default: 80)
            timeout: Request timeout in seconds (default: 10)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GET request to the matrix device.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Dictionary containing status code and response text

        Raises:
            MatrixConnectionError: If unable to connect to device
            MatrixTimeoutError: If request times out
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:  # noqa: SIM117
                async with session.get(url, params=params) as response:
                    text = await response.text()
                    return {
                        "status": response.status,
                        "text": text,
                        "headers": dict(response.headers),
                    }
        except asyncio.TimeoutError as e:  # noqa: UP041
            raise MatrixTimeoutError(
                f"Request to {url} timed out after {self.timeout}s"
            ) from e
        except aiohttp.ClientConnectionError as e:
            raise MatrixConnectionError(
                f"Failed to connect to {self.host}:{self.port}"
            ) from e
        except aiohttp.ClientError as e:
            raise MatrixConnectionError(
                f"Connection error to {self.host}:{self.port}: {e}"
            ) from e

    async def send_command(self, command: str, **kwargs) -> bool:
        """Send a command to the matrix device.

        Args:
            command: Command to execute
            **kwargs: Additional command parameters

        Returns:
            Boolean indicating success of HTTP request (2xx = True, else False)

        Raises:
            MatrixCommandError: If command fails
        """
        SUBMIT_ENDPOINT = "/cgi-bin/submit"  # noqa: N806

        # Build query parameters with command and any additional kwargs
        params = {"cmd": command}
        params.update(kwargs)

        try:
            response = await self.get(SUBMIT_ENDPOINT, params=params)
            # Check if response status is successful (2xx)
            return 200 <= response["status"] < 300
        except (MatrixConnectionError, MatrixTimeoutError) as e:
            raise MatrixCommandError(f"Failed to send command '{command}': {e}") from e
