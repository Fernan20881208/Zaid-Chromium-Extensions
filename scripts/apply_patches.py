#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil
import subprocess

from common import ROOT, run


def series():
    names = [line.strip() for line in (ROOT / "patches/series").read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not names or len(names) != len(set(names)):
        raise ValueError("Patch series must be nonempty and unique")
    for name in names:
        if Path(name).name != name or not name.endswith(".patch"):
            raise ValueError(f"Invalid patch path: {name}")
    return [ROOT / "patches" / name for name in names]


def apply(source):
    for patch in series():
        check = subprocess.run(["git", "apply", "--check", str(patch)],
                               cwd=source, capture_output=True, text=True)
        if check.returncode:
            reverse = subprocess.run(["git", "apply", "--reverse", "--check", str(patch)],
                                     cwd=source, capture_output=True, text=True)
            if reverse.returncode == 0:
                print(f"Already applied: {patch.name}")
                continue
            raise RuntimeError(f"Patch drift in {patch.name}:\n{check.stderr}")
        run("git", "apply", "--whitespace=error-all", patch, cwd=source)
        print(f"Applied: {patch.name}")
    overlay = ROOT / "src"
    for item in sorted(overlay.rglob("*")):
        if not item.is_file() or item.name == "README.md":
            continue
        destination = source / item.relative_to(overlay)
        if destination.exists() and destination.read_bytes() != item.read_bytes():
            raise RuntimeError(f"Refusing to overwrite different overlay file: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    apply(args.source.resolve())


if __name__ == "__main__":
    main()
