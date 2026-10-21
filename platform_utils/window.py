"""Stub Windows - implementar en Fase 1 avanzada."""
from .base import PlatformNotSupportedError, WindowProvider


class WindowsProvider(WindowProvider):
    platform_id = "windows"

    def get_active_window(self):
        raise PlatformNotSupportedError("WindowsProvider no implementado aún")

    def get_idle_seconds(self):
        raise PlatformNotSupportedError("WindowsProvider no implementado aún")


def create_provider() -> WindowProvider:
    return WindowsProvider()