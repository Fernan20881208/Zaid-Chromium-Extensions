#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shutil

from apply_patches import apply
from common import ROOT, build_env, revision, run
from preflight import inspect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=ROOT / "work")
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 2, 8))
    parser.add_argument("--skip-sync", action="store_true")
    parser.add_argument("--install-deps", action="store_true")
    parser.add_argument("--configure-only", action="store_true")
    parser.add_argument("--no-package", action="store_true")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("jobs must be positive")
    work = args.work.resolve()
    check = inspect(work, disk_gib=40 if args.skip_sync else 100)
    if not check["ready"]:
        raise SystemExit("\n".join(check["problems"]))
    if not args.skip_sync:
        run("python3", ROOT / "scripts/sync_chromium.py", "--work", work)
    source = work / "src"
    lock = revision()
    head = run("git", "rev-parse", "HEAD", cwd=source, capture=True).strip()
    if head != lock["commit"]:
        raise SystemExit("Source HEAD differs from chromium/revision.json")
    if args.install_deps:
        run("sudo", "-n", "bash", source / "build/install-build-deps.sh", "--android", "--no-prompt")
    env = build_env(work)
    run("gclient", "runhooks", cwd=work, env=env)
    apply(source)
    out = source / "out/ZaidArm64"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "chromium/args.gn", out / "args.gn")
    run("gn", "gen", out, "--fail-on-unused-args", "--check", cwd=source, env=env)
    if args.configure_only:
        return
    run("autoninja", "-C", out, f"-j{args.jobs}", "chrome_public_apk", cwd=source, env=env)
    if not args.no_package:
        run("python3", ROOT / "scripts/package_apk.py", "--work", work)


if __name__ == "__main__":
    main()
