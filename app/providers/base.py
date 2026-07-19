from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderCapabilities:
    selected_library: bool = True
    per_app_jobs: bool = False
    structured_progress: bool = False
    manifest_tracking: bool = False
    depot_tracking: bool = False
    native_pause_resume: bool = False
    cache_object_index: bool = False
    per_game_purge: bool = False

    def model_dump(self) -> dict[str, bool]:
        return asdict(self)


class PrefillProvider(ABC):
    provider_id: str
    display_name: str
    compatibility_mode: bool = True
    capabilities: ProviderCapabilities

    @property
    @abstractmethod
    def working_directory(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def container_user(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def select_games_command(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def status_command(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def clear_cache_command(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def schedule_keys(self) -> tuple[str, ...]:
        raise NotImplementedError

    @property
    @abstractmethod
    def selected_app_config_candidates(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def managed_prefill_command(self, app_id: int | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def process_match_shell(self, variable: str = "$cmdline") -> str:
        """Return a shell condition that succeeds for a provider prefill process."""
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": self.display_name,
            "compatibility_mode": self.compatibility_mode,
            "capabilities": self.capabilities.model_dump(),
        }
