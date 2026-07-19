from __future__ import annotations

from app.providers.base import PrefillProvider, ProviderCapabilities
from app.providers.steamprefill import SteamPrefillProvider


def create_provider(
    provider_id: str,
    *,
    working_directory: str,
    container_user: str,
    command: str,
) -> PrefillProvider:
    normalised = (provider_id or "steamprefill").strip().casefold()
    if normalised != "steamprefill":
        raise ValueError(
            f"Unsupported CACHEDECK_PROVIDER={provider_id!r}. v0.7 ships the "
            "SteamPrefill compatibility provider; the native Steam provider arrives in v0.8."
        )
    return SteamPrefillProvider(
        working_directory=working_directory,
        container_user=container_user,
        command=command,
    )


__all__ = [
    "PrefillProvider",
    "ProviderCapabilities",
    "SteamPrefillProvider",
    "create_provider",
]
