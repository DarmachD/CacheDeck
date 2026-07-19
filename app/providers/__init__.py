from __future__ import annotations

from app.providers.base import PrefillProvider, ProviderCapabilities
from app.providers.embedded_steam import EmbeddedSteamProvider
from app.providers.steamprefill import SteamPrefillProvider


def create_provider(
    provider_id: str,
    *,
    working_directory: str,
    container_user: str,
    command: str,
    embedded_binary: str = "/opt/steamprefill/SteamPrefill",
) -> PrefillProvider:
    normalised = (provider_id or "embedded-steam").strip().casefold()
    if normalised in {"embedded", "embedded-steam", "native", "native-steam"}:
        return EmbeddedSteamProvider(
            working_directory=working_directory,
            command=command,
            binary=embedded_binary,
        )
    if normalised == "steamprefill":
        return SteamPrefillProvider(
            working_directory=working_directory,
            container_user=container_user,
            command=command,
        )
    raise ValueError(
        f"Unsupported CACHEDECK_PROVIDER={provider_id!r}. Choose embedded-steam "
        "for CacheDeck's bundled engine or steamprefill for the legacy target-container provider."
    )


__all__ = [
    "EmbeddedSteamProvider",
    "PrefillProvider",
    "ProviderCapabilities",
    "SteamPrefillProvider",
    "create_provider",
]
