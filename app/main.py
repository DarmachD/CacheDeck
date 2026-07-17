from __future__ import annotations

import asyncio
import contextlib
import os
import pty
import select
import signal
import struct
import subprocess
import termios
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

APP_NAME: Final = "CacheDeck"
APP_VERSION: Final = os.getenv("CACHEDECK_VERSION", "0.3.0")

TARGET_CONTAINER: Final = os.getenv("TARGET_CONTAINER", "LANCache-Prefill")
PREFILL_DIR: Final = os.getenv(
    "PREFILL_DIR",
    "/lancacheprefill/SteamPrefill",
)
PREFILL_USER: Final = os.getenv("PREFILL_USER", "prefill")

STATIC_DIR: Final = Path(__file__).resolve().parent / "static"

ALLOWED_ACTIONS: Final[dict[str, str]] = {
    "status": "./SteamPrefill status",
    "clear-cache": "./SteamPrefill clear-cache -y",
}

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url=None,
)


class ActionRequest(BaseModel):
    action: str


class CommandResult(BaseModel):
    ok: bool
    code: int
    stdout: str
    stderr: str


def docker_exec_command(command: str, *, interactive: bool = False) -> list[str]:
    """Build a docker exec command for the configured SteamPrefill container."""
    args = ["docker", "exec"]

    if interactive:
        args.extend(["-i", "-t"])

    if PREFILL_USER:
        args.extend(["--user", PREFILL_USER])

    if PREFILL_DIR:
        args.extend(["--workdir", PREFILL_DIR])

    args.extend(
        [
            TARGET_CONTAINER,
            "bash",
            "-lc",
            command,
        ]
    )
    return args


def run_process(
    args: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


async def run_process_async(
    args: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(run_process, args, timeout=timeout)


async def inspect_target() -> dict[str, str | bool]:
    try:
        result = await run_process_async(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Running}}|{{.State.Status}}",
                TARGET_CONTAINER,
            ],
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return {
            "running": False,
            "status": "timeout",
            "detail": "Docker did not answer within 10 seconds.",
        }
    except OSError as exc:
        return {
            "running": False,
            "status": "error",
            "detail": str(exc),
        }

    if result.returncode != 0:
        return {
            "running": False,
            "status": "not found",
            "detail": result.stderr.strip() or "Target container was not found.",
        }

    raw = result.stdout.strip()
    running_text, _, status = raw.partition("|")

    return {
        "running": running_text == "true",
        "status": status or "unknown",
        "detail": "",
    }


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.svg", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "favicon.svg",
        media_type="image/svg+xml",
    )


@app.get("/api/health")
async def health() -> dict[str, object]:
    target = await inspect_target()
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "target": TARGET_CONTAINER,
        "prefill_dir": PREFILL_DIR,
        "prefill_user": PREFILL_USER,
        "running": target["running"],
        "status": target["status"],
        "detail": target["detail"],
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/logs")
async def logs(
    lines: int = Query(default=150, ge=10, le=2000),
) -> CommandResult:
    try:
        result = await run_process_async(
            [
                "docker",
                "logs",
                "--tail",
                str(lines),
                TARGET_CONTAINER,
            ],
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail="Timed out while reading the target container logs.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to run Docker: {exc}",
        ) from exc

    return CommandResult(
        ok=result.returncode == 0,
        code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


@app.post("/api/action")
async def action(request: ActionRequest) -> CommandResult:
    command = ALLOWED_ACTIONS.get(request.action)

    if command is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported action.",
        )

    try:
        result = await run_process_async(
            docker_exec_command(command),
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail="SteamPrefill did not finish within five minutes.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to run Docker: {exc}",
        ) from exc

    return CommandResult(
        ok=result.returncode == 0,
        code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


@app.websocket("/ws/terminal")
async def terminal(websocket: WebSocket) -> None:
    await websocket.accept()

    target = await inspect_target()
    if not target["running"]:
        await websocket.send_text(
            "\r\n\x1b[31mCacheDeck could not connect to "
            f"{TARGET_CONTAINER}: {target['status']}.\x1b[0m\r\n"
        )
        await websocket.close(code=1011)
        return

    master_fd, slave_fd = pty.openpty()

    # Give applications a sensible size before the browser sends its first resize.
    import fcntl

    fcntl.ioctl(
        master_fd,
        termios.TIOCSWINSZ,
        struct.pack("HHHH", 40, 120, 0, 0),
    )

    environment = os.environ.copy()
    environment["TERM"] = "xterm-256color"

    try:
        process = subprocess.Popen(
            docker_exec_command("exec bash", interactive=True),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=environment,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as exc:
        os.close(master_fd)
        os.close(slave_fd)
        await websocket.send_text(
            f"\r\n\x1b[31mUnable to start Docker terminal: {exc}\x1b[0m\r\n"
        )
        await websocket.close(code=1011)
        return

    os.close(slave_fd)

    async def pump_output() -> None:
        loop = asyncio.get_running_loop()

        while process.poll() is None:
            ready, _, _ = await loop.run_in_executor(
                None,
                lambda: select.select([master_fd], [], [], 0.2),
            )
            if not ready:
                continue

            try:
                data = os.read(master_fd, 8192)
            except OSError:
                break

            if not data:
                break

            try:
                await websocket.send_bytes(data)
            except RuntimeError:
                break

    output_task = asyncio.create_task(pump_output())

    try:
        while True:
            message = await websocket.receive()

            text = message.get("text")
            if text is not None:
                if text.startswith("__RESIZE__:"):
                    try:
                        _, columns, rows = text.split(":", 2)
                        fcntl.ioctl(
                            master_fd,
                            termios.TIOCSWINSZ,
                            struct.pack(
                                "HHHH",
                                int(rows),
                                int(columns),
                                0,
                                0,
                            ),
                        )
                    except (ValueError, OSError):
                        pass
                else:
                    os.write(master_fd, text.encode("utf-8"))
                continue

            data = message.get("bytes")
            if data is not None:
                os.write(master_fd, data)

    except WebSocketDisconnect:
        pass
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(
                asyncio.to_thread(process.wait),
                timeout=3,
            )

        if process.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)

        output_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await output_task

        with contextlib.suppress(OSError):
            os.close(master_fd)
