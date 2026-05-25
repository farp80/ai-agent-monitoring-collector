"""Shared subprocess helpers for platform providers."""

from __future__ import annotations

import subprocess
from typing import Sequence


def run_command(
    args: Sequence[str],
    *,
    timeout: float = 30.0,
    shell: bool = False,
) -> str | None:
    try:
        result = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip()
