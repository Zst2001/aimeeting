from dataclasses import dataclass


@dataclass
class AppException(Exception):
    """Base exception for expected application errors."""

    message: str
    code: int
    status_code: int = 400
