"""Custom exceptions for HDMI Matrix Control library."""


class MatrixControlException(Exception):
    """Base exception for all HDMI Matrix Control errors."""


class MatrixConnectionError(MatrixControlException):
    """Raised when unable to establish or maintain connection to matrix."""


class MatrixCommandError(MatrixControlException):
    """Raised when a command execution fails."""


class MatrixTimeoutError(MatrixControlException):
    """Raised when a command times out."""
