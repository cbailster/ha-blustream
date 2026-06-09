"""Configuration management for HDMI Matrix Control library."""

from dataclasses import dataclass


@dataclass
class DeviceConfig:
    """Configuration for HDMI matrix device."""

    host: str
    http_port: int = 80
    timeout: int = 10

    def __post_init__(self):
        """Validate configuration."""
        if not self.host:
            raise ValueError("Host must be specified")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


@dataclass
class OutputStatus:
    """Status of an output port."""

    output_port: int
    name: str | None = None
    input_port: int | None = None
    audio_input_port: str | None = None
    status: bool | None = None


@dataclass
class InputStatus:
    """Status of an input port."""

    input_port: int
    name: str | None = None
    status: bool | None = None


@dataclass
class MatrixInfo:
    """Information about the matrix device."""

    AUDIO_TYPES = {
        "ana": "Analog Audio",
        "ext": "HDMI Audio",
        "arc": "Audio Return Channel",
    }

    model: str | None = None
    firmware_version: str | None = None
    input_count: int | None = None
    output_count: int | None = None
    power: bool | None = None

    inputs: list[InputStatus] | None = None
    outputs: list[OutputStatus] | None = None

    @property
    def input_names(self) -> dict[int, str] | None:
        """Get input names mapped by input port number."""
        if not self.inputs:
            return None
        return {inp.input_port: inp.name.replace("_", " ") for inp in self.inputs if inp.name} or None

    @property
    def output_names(self) -> dict[int, str] | None:
        """Get output names mapped by output port number."""
        if not self.outputs:
            return None
        return {out.output_port: out.name.replace("_", " ") for out in self.outputs if out.name} or None

    @property
    def audio_input_options(self) -> dict | None:
        """Get available audio input options that can be selected for an output port."""
        common_audio_inputs = {
            "foext": "Follow Selected Input - Extract from Video",
            "foana": "Follow Selected Input - Analog Audio",
        }
        for key, label in self.AUDIO_TYPES.items():
            if key == "arc":
                name_source = self.output_names or {}
            else:
                name_source = self.input_names or {}
            for input_id, input_name in name_source.items():
                if input_id <= (
                    self.input_count or 0
                ):  # Ensure input_id is within valid range
                    common_audio_inputs[f"{key} {input_id}"] = f"{label} - {input_name}"
        return common_audio_inputs or None

    def input_from_name(self, name: str) -> int | None:
        """Get input port number from input name."""
        if not self.inputs:
            return None
        for inp in self.inputs:
            if inp.name and inp.name.replace("_", " ") == name:
                return inp.input_port
        return None

    def audio_input_from_name(self, name: str) -> str | None:
        """Get audio input option from name."""
        options = self.audio_input_options or {}
        for option_key, option_label in options.items():
            if option_label == name:
                return option_key
        return None