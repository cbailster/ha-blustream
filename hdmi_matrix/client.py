"""Main HDMI Matrix Client for high-level control operations."""

from typing import Any

import defusedxml.ElementTree as ET
from defusedxml.ElementTree import fromstring

from .config import InputStatus, MatrixInfo, OutputStatus
from .exceptions import MatrixCommandError, MatrixConnectionError, MatrixTimeoutError
from .http_client import HTTPClient


class HDMIMatrixClient:
    """Main client for controlling HDMI matrix devices.

    Supports both HTTP and Telnet protocols for device communication.

    Attributes:
        host: IP address or hostname of the matrix device
        connection_type: Type of connection to use (HTTP or TELNET)
    """

    def __init__(self, host: str, http_port: int = 80, timeout: int = 10) -> None:
        """Initialize HDMI Matrix Client.

        Args:
            host: IP address or hostname of the matrix device
            http_port: HTTP port if using HTTP (default: 80)
            timeout: Connection timeout in seconds (default: 10)

        Raises:
            ValueError: If invalid connection type specified
        """
        self.host = host
        self.timeout = timeout

        self.client = HTTPClient(host, http_port, timeout)
        self.matrix_info = MatrixInfo()

    def _extract_xml_value(
        self, element: ET.Element | None, converter=None
    ) -> Any | None:
        """Extract and optionally convert value from an XML element.

        Args:
            element: XML element to extract from
            converter: Optional function to convert the extracted text (e.g., int, str)

        Returns:
            Converted value or None if element is missing or has no text
        """
        if element is None or element.text is None:
            return None
        return converter(element.text) if converter else element.text

    def _parse_audio_types(self, root: ET.Element) -> str | None:
        """Parse audio input options from the XML response.

        Args:
            root: Root element of the XML response containing output device information

        Returns:
            name of the audio output option that maps to the audio_input_options dictionary from the MatrixInfo class, or None if no match is found
        """
        TYPE_MAP: list[str] = ["ana", "ext", "arc", "foana", "foext"]  # noqa: N806

        audio_type_id = self._extract_xml_value(root.find("audtype"), int)
        audio_input_id = self._extract_xml_value(root.find("audport"), int)
        if audio_type_id is not None and 0 <= audio_type_id <= 2:
            return f"{TYPE_MAP[audio_type_id]} {audio_input_id}"
        if (
            audio_type_id is not None
            and audio_type_id >= 3
            and audio_type_id < len(TYPE_MAP)
        ):
            return TYPE_MAP[audio_type_id]

        return None

    async def get_device_info(self):
        """Get device information from the matrix.

        Raises:
            MatrixConnectionError: If not connected
            MatrixCommandError: If command fails
        """
        GETXML_ENDPOINT = "/cgi-bin/getxml.cgi"  # noqa: N806

        try:
            # Fetch the XML response
            response = await self.client.get(GETXML_ENDPOINT, params={"xml": "mxsta"})

            # Check status code
            if response["status"] != 200:
                raise MatrixCommandError(  # noqa: TRY301
                    f"Failed to get device info: HTTP {response['status']}"
                )

            # Parse XML response
            root = fromstring(response["text"])

            # Create MatrixInfo object and populate with XPath queries
            self.matrix_info.model = self._extract_xml_value(
                root.find(".//mxsta/devname")
            )
            self.matrix_info.firmware_version = self._extract_xml_value(
                root.find(".//mxsta/softver")
            )
            self.matrix_info.input_count = self._extract_xml_value(
                root.find(".//mxsta/inputport"), int
            )
            self.matrix_info.output_count = self._extract_xml_value(
                root.find(".//mxsta/outputport"), int
            )
            self.matrix_info.power = self._extract_xml_value(
                root.find(".//mxsta/power"), lambda x: x == "1"
            )

            # Populate inputs list with InputStatus objects
            input_elements = root.findall(".//input")
            self.matrix_info.inputs = [
                InputStatus(
                    input_port=index,
                    name=self._extract_xml_value(input_elem.find("name")),
                    status=(
                        self._extract_xml_value(input_elem.find("hdmi5v")) == "1"
                        or self._extract_xml_value(input_elem.find("hdbt5v")) == "1"
                    ),
                )
                for index, input_elem in enumerate(input_elements, start=1)
                if index <= (self.matrix_info.input_count or float("inf"))
            ] or None

            # Populate outputs list with OutputStatus objects
            output_elements = root.findall(".//output")
            self.matrix_info.outputs = [
                OutputStatus(
                    output_port=index,
                    name=self._extract_xml_value(output_elem.find("name")),
                    status=self._extract_xml_value(output_elem.find("outputen")) == "1",
                    input_port=(
                        self._extract_xml_value(output_elem.find("from"), int) or 0 + 1
                    )
                    if self._extract_xml_value(output_elem.find("from"))
                    else None,
                    audio_input_port=self._parse_audio_types(output_elem),
                )
                for index, output_elem in enumerate(output_elements, start=1)
                if index <= (self.matrix_info.output_count or float("inf"))
            ] or None

        except MatrixCommandError:
            raise
        except (MatrixConnectionError, MatrixTimeoutError) as e:
            raise MatrixCommandError(f"Failed to retrieve device info: {e}") from e
        except ET.ParseError as e:
            raise MatrixCommandError(f"Failed to parse device XML response: {e}") from e

    async def set_power(self, on: bool) -> bool:
        """Set power state of the matrix device.

        Args:
            on: True to power on, False to power off

        Returns:
            True if command was successful, False otherwise

        Raises:
            MatrixConnectionError: If not connected
            MatrixCommandError: If command fails
        """
        return await self.client.send_command("pon" if on else "poff")

    async def set_input(self, output_port: int, input_port: int) -> bool:
        """Set input source for a specific output port.

        Args:
            output_port: Output port number (1-based)
            input_port: Input port number (1-based)

        Returns:
            True if command was successful, False otherwise

        Raises:
            MatrixConnectionError: If not connected
            MatrixCommandError: If command fails
        """
        return await self.client.send_command(f"out{output_port:02d}fr{input_port:02d}")

    async def set_audio_input(self, output_port: int, audio_input: str) -> bool:
        """Set audio input source for a specific output port.

        Args:
            output_port: Output port number (1-based)
            audio_input: Audio input source (e.g., 'ana 1', 'ext 2', 'arc 3', 'foana', 'foext')

        Returns:
            True if command was successful, False otherwise

        Raises:
            MatrixConnectionError: If not connected
            MatrixCommandError: If command fails
        """
        return await self.client.send_command(f"aud tx {output_port:02d} {audio_input}")

    async def set_output_status(self, output_port: int, enabled: bool) -> bool:
        """Enable/Disable output on a specific port.

        Args:
            output_port: Output port number (1-based)
            enabled: True to enable output, False to disable output

        Returns:
            True if command was successful, False otherwise

        Raises:
            MatrixConnectionError: If not connected
            MatrixCommandError: If command fails
        """
        return await self.client.send_command(
            f"out{output_port:02d}fr{'on' if enabled else 'off'}"
        )

    def connect(self) -> None:
        """Establish connection to the matrix device."""
        # Implementation to be completed
        pass  # noqa: PIE790

    def disconnect(self) -> None:
        """Close connection to the matrix device."""
        # Implementation to be completed
        pass  # noqa: PIE790

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
