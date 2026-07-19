#!/usr/bin/env bash
set -euo pipefail
umask 077

engine_dir="${CACHEDECK_STEAM_ENGINE_DIR:-/config/steam-engine}"
engine_binary="${CACHEDECK_STEAM_ENGINE_BINARY:-${engine_dir}/SteamPrefill}"
source_dir="/opt/steamprefill"

mkdir -p "${engine_dir}" "${PREFILL_STATE_DIR:-${engine_dir}/state}"

# Keep the official engine files current while preserving the persistent Config
# directory and any account/session data already created by SteamPrefill.
for source in "${source_dir}"/*; do
    [[ -f "${source}" ]] || continue
    destination="${engine_dir}/$(basename "${source}")"
    if [[ ! -f "${destination}" ]] || ! cmp -s "${source}" "${destination}"; then
        cp -f "${source}" "${destination}"
    fi
done
chmod 0755 "${engine_binary}"

if [[ "$#" -gt 0 ]]; then
    exec "$@"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
