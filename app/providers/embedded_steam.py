from __future__ import annotations

import shlex

from app.providers.base import PrefillProvider, ProviderCapabilities


class EmbeddedSteamProvider(PrefillProvider):
    """Steam prefill engine shipped inside the CacheDeck image.

    v0.8 embeds the proven SteamPrefill download core so CacheDeck can own the
    process, state directory and logs without requiring a second Docker
    container. The provider boundary remains in place so the implementation can
    move to CacheDeck's direct SteamKit worker incrementally.
    """

    provider_id = "embedded-steam"
    display_name = "CacheDeck embedded Steam engine (beta)"
    compatibility_mode = False
    execution_mode = "local"
    requires_docker_socket = False
    capabilities = ProviderCapabilities(
        selected_library=True,
        per_app_jobs=True,
        structured_progress=False,
        manifest_tracking=False,
        depot_tracking=False,
        native_pause_resume=False,
        cache_object_index=False,
        per_game_purge=False,
    )

    def __init__(self, *, working_directory: str, command: str, binary: str) -> None:
        self._working_directory = working_directory
        self._binary = binary.strip() or "/opt/steamprefill/SteamPrefill"
        self._command = command.strip() or f"{shlex.quote(self._binary)} prefill"

    @property
    def working_directory(self) -> str:
        return self._working_directory

    @property
    def container_user(self) -> str:
        return ""

    @property
    def binary(self) -> str:
        return self._binary

    @property
    def select_games_command(self) -> str:
        return f"{shlex.quote(self._binary)} select-apps"

    @property
    def status_command(self) -> str:
        return f"{shlex.quote(self._binary)} select-apps status --no-ansi"

    @property
    def clear_cache_command(self) -> str:
        return f"{shlex.quote(self._binary)} clear-cache -y"

    @property
    def schedule_keys(self) -> tuple[str, ...]:
        # CacheDeck owns schedules for the embedded engine.
        return ()

    @property
    def selected_app_config_candidates(self) -> tuple[str, ...]:
        return (
            "./Config/selectedAppsToPrefill.json",
            f"{self._working_directory.rstrip('/')}/Config/selectedAppsToPrefill.json",
        )

    @property
    def downloaded_state_candidates(self) -> tuple[str, ...]:
        return (
            "./Config/successfullyDownloadedDepots.json",
            f"{self._working_directory.rstrip('/')}/Config/successfullyDownloadedDepots.json",
        )

    def managed_prefill_command(self, app_id: int | None = None) -> str:
        parts = shlex.split(self._command)
        if app_id is not None:
            try:
                prefill_index = parts.index("prefill")
            except ValueError:
                parts.extend(["prefill", str(app_id)])
            else:
                parts.insert(prefill_index + 1, str(app_id))
        if "--verbose" not in parts:
            parts.append("--verbose")
        if "--no-ansi" not in parts:
            parts.append("--no-ansi")
        return shlex.join(parts)

    def process_match_shell(self, variable: str = "$cmdline") -> str:
        binary_name = shlex.quote(self._binary.rsplit("/", 1)[-1])
        return f'[[ {variable} =~ {binary_name}.*[[:space:]]prefill([[:space:]]|$) ]]'
