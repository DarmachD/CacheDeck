# CacheDeck

CacheDeck is a browser control panel for an existing
[SteamPrefill](https://github.com/tpill90/steam-lancache-prefill) container.

It provides a cleaner interface for selecting games, starting prefill jobs,
checking status, reading logs and using SteamPrefill's interactive terminal.

## Current features

- Browser-based SteamPrefill game selector
- One-click game selection and prefill controls
- Live interactive terminal
- Target-container health information
- Recent SteamPrefill logs
- Docker and Unraid Community Applications packaging
- Automatic GHCR builds from GitHub Actions

CacheDeck intentionally uses SteamPrefill's maintained interactive selector
instead of recreating Steam authentication and catalogue logic.

## Requirements

- A working SteamPrefill Docker container
- Access to `/var/run/docker.sock`
- The SteamPrefill path and user used by the target container
- A trusted LAN; CacheDeck should not be exposed directly to the internet

## Docker Compose

```yaml
services:
  cachedeck:
    image: ghcr.io/darmachd/cachedeck:latest
    container_name: CacheDeck
    restart: unless-stopped
    ports:
      - "8088:8080"
    environment:
      TARGET_CONTAINER: LANCache-Prefill
      PREFILL_DIR: /lancacheprefill/SteamPrefill
      PREFILL_USER: prefill
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

Open `http://YOUR-SERVER-IP:8088`.

## Unraid

The Community Applications template is:

```text
templates/cachedeck.xml
```

Before public submission:

1. Push the repository to GitHub.
2. Confirm the GitHub Actions build succeeds.
3. Make the `ghcr.io/darmachd/cachedeck` package public.
4. Test the template privately on Unraid.
5. Run Validate and Scan in the Unraid Community Apps submission portal.
6. Submit the repository for review after all checks pass.

## Development

Create a Python 3.13 virtual environment and install the requirements:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The app needs the Docker socket and a Linux PTY for its terminal, so the complete
terminal workflow is best tested inside Docker or directly on Unraid.

## Security

Mounting the Docker socket provides powerful control over the Docker host.
CacheDeck has no built-in authentication in this release. Keep it accessible
only from trusted networks.

## Licence

MIT. Copyright © 2026 Danny.
