#!/usr/bin/env bash
set -euo pipefail
umask 077

engine_dir="${CACHEDECK_STEAM_ENGINE_DIR:-${CACHEDECK_CONFIG_DIR:-/config}/steam-engine}"
engine_binary="${CACHEDECK_STEAM_ENGINE_BINARY:-${engine_dir}/SteamPrefill}"
state_dir="${PREFILL_STATE_DIR:-${engine_dir}/state}"
source_dir="/opt/steamprefill"
source_binary="${source_dir}/SteamPrefill"

if [[ ! -x "${source_binary}" ]]; then
    echo "CacheDeck embedded Steam engine is missing: ${source_binary}" >&2
    exit 1
fi

mkdir -p "${engine_dir}" "${state_dir}" "$(dirname "${engine_binary}")"

# Keep the packaged engine current while preserving the persistent Config
# directory and any Steam account/session data created at runtime.
for source in "${source_dir}"/*; do
    [[ -f "${source}" ]] || continue
    destination="${engine_dir}/$(basename "${source}")"
    if [[ ! -f "${destination}" ]] || ! cmp -s "${source}" "${destination}"; then
        cp -f "${source}" "${destination}"
    fi
done

# A custom binary path is supported, but the normal path remains inside the
# persistent engine directory. Copy the packaged executable there explicitly
# when the paths differ.
default_binary="${engine_dir}/SteamPrefill"
if [[ "${engine_binary}" != "${default_binary}" ]]; then
    if [[ ! -f "${engine_binary}" ]] || ! cmp -s "${source_binary}" "${engine_binary}"; then
        cp -f "${source_binary}" "${engine_binary}"
    fi
fi
chmod 0755 "${default_binary}" "${engine_binary}"

if [[ "$#" -gt 0 ]]; then
    exec "$@"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
