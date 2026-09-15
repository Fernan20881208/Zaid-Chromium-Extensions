from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def revision():
    value = json.loads((ROOT / "chromium/revision.json").read_text())
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", value["version"]):
        raise ValueError("Invalid Chromium version")
    for key in ("commit", "depot_tools_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", value[key]):
            raise ValueError(f"Invalid {key}")
    return value


def run(*args, cwd=None, capture=False, env=None):
    return subprocess.run(
        [str(arg) for arg in args], cwd=cwd, check=True,
        text=True, capture_output=capture, env=env,
    ).stdout


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Zaid-Chromium-Build/1"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def build_env(work):
    env = os.environ.copy()
    env.update({
        "PATH": str(work / "depot_tools") + os.pathsep + env["PATH"],
        "DEPOT_TOOLS_UPDATE": "0",
        "DEPOT_TOOLS_METRICS": "0",
        "DEPOT_TOOLS_WIN_TOOLCHAIN": "0",
    })
    return env
