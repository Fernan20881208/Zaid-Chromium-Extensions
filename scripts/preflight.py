#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys


def inspect(path, disk_gib=100, ram_gib=16):
    probe = path.resolve()
    while not probe.exists():
        probe = probe.parent
    free = shutil.disk_usage(probe).free / 1024**3
    ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
    problems = []
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        problems.append("Use an x86_64 Ubuntu 22.04/24.04 build host; APK target remains ARM64.")
    if free < disk_gib:
        problems.append(f"Need {disk_gib} GiB free for source, dependencies and output; found {free:.1f}.")
    if ram < ram_gib * 0.95:
        problems.append(f"Need {ram_gib} GiB RAM; found {ram:.1f}. Recommend 32 GiB or more.")
    return {"free_disk_gib": round(free, 1), "ram_gib": round(ram, 1),
            "cpu_count": os.cpu_count(), "ready": not problems, "problems": problems}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=Path("work"))
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    result = inspect(args.work)
    print(json.dumps(result, indent=2))
    if not result["ready"] and not args.report_only:
        print("Set repository variable CHROMIUM_RUNNER to a suitable Ubuntu runner label or JSON label array.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
