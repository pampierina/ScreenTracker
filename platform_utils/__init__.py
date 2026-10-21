"""Utilidades específicas de plataforma para ScreenTracker."""

from .base import (
    ActiveWindow,
    PlatformNotSupportedError,
    WindowDetectionError,
    WindowProvider,
    get_provider,
    reset_provider,
)

__all__ = [
    "ActiveWindow",
    "PlatformNotSupportedError",
    "WindowDetectionError",
    "WindowProvider",
    "get_provider",
    "reset_provider",
]