"""Backend API for Aldockery."""
from __future__ import annotations

import shlex
import subprocess
from typing import Any

from .const import (
    CONF_DOCKER_BIN,
    CONF_MODE,
    CONF_SSH_HOST,
    CONF_SSH_KEY,
    CONF_SSH_PORT,
    CONF_SSH_USER,
    DEFAULT_DOCKER_BIN,
    DEFAULT_SSH_PORT,
    MODE_LOCAL,
    MODE_SSH,
)


class AldockeryAPI:
    """Talk to Docker locally or over SSH."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def _run(self, cmd: list[str], timeout: int = 60) -> str:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stdout or "").strip() or f"Command failed: {' '.join(cmd)}")
        return (result.stdout or "").strip()

    def _docker_exec(self, args: list[str], timeout: int = 60) -> str:
        docker_bin = self._config.get(CONF_DOCKER_BIN, DEFAULT_DOCKER_BIN)
        mode = self._config[CONF_MODE]

        if mode == MODE_LOCAL:
            return self._run([docker_bin] + args, timeout=timeout)

        if mode == MODE_SSH:
            ssh_port = int(self._config.get(CONF_SSH_PORT, DEFAULT_SSH_PORT))
            remote = shlex.quote(docker_bin) + " " + " ".join(shlex.quote(a) for a in args)
            cmd = [
                "ssh",
                "-i", self._config[CONF_SSH_KEY],
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=accept-new",
                "-p", str(ssh_port),
                f"{self._config[CONF_SSH_USER]}@{self._config[CONF_SSH_HOST]}",
                remote,
            ]
            return self._run(cmd, timeout=timeout)

        raise ValueError(f"Unsupported mode: {mode}")

    def test_connection(self) -> str:
        return self._docker_exec(["version", "--format", "{{.Server.Version}}"], timeout=20)

    def list_containers(self) -> dict[str, dict[str, Any]]:
        out = self._docker_exec(
            ["ps", "-a", "--format", "{{.Names}}|{{.State}}|{{.Status}}|{{.Image}}"],
            timeout=60,
        )
        data: dict[str, dict[str, Any]] = {}
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) != 4:
                continue
            name, state, status, image = parts
            data[name] = {
                "name": name,
                "state": state,
                "status": status,
                "image": image,
            }
        return data

    def start_container(self, container: str) -> str:
        return self._docker_exec(["start", container], timeout=120)

    def stop_container(self, container: str) -> str:
        return self._docker_exec(["stop", container], timeout=120)

    def restart_container(self, container: str) -> str:
        return self._docker_exec(["restart", container], timeout=120)
