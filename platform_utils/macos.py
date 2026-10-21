"""Stub macOS - implementar en Fase 1 avanzada."""
from .base import PlatformNotSupportedError, WindowProvider


class MacOSProvider(WindowProvider):
    platform_id = "macos"

    def get_active_window(self):
        raise PlatformNotSupportedError("MacOSProvider no implementado aún")

    def get_idle_seconds(self):
        raise PlatformNotSupportedError("MacOSProvider no implementado aún")


def create_provider() -> WindowProvider:
    return MacOSProvider()