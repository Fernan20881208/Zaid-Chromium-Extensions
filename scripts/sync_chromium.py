#!/usr/bin/env python3
import argparse
from pathlib import Path

from common import ROOT, build_env, revision, run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=ROOT / "work")
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("jobs must be positive")
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    lock = revision()
    depot = work / "depot_tools"
    if not (depot / ".git").exists():
        depot.mkdir(exist_ok=True)
        run("git", "init", depot)
        run("git", "remote", "add", "origin",
            "https://chromium.googlesource.com/chromium/tools/depot_tools.git", cwd=depot)
    if run("git", "status", "--porcelain", cwd=depot, capture=True).strip():
        raise SystemExit("depot_tools contains local edits; use a clean work directory.")
    run("git", "fetch", "--depth=1", "origin", lock["depot_tools_commit"], cwd=depot)
    run("git", "checkout", "--detach", "FETCH_HEAD", cwd=depot)

    source = work / "src"
    if (source / ".git").exists():
        if run("git", "status", "--porcelain", "--untracked-files=no", cwd=source, capture=True).strip():
            raise SystemExit("Chromium has local edits/patches. Reuse with --skip-sync, or choose a new --work directory.")
    else:
        source.mkdir(exist_ok=True)
        run("git", "init", source)
        run("git", "remote", "add", "origin", lock["repository"], cwd=source)
    run("git", "fetch", "--depth=1", "origin", f"refs/tags/{lock['version']}", cwd=source)
    actual = run("git", "rev-parse", "FETCH_HEAD^{commit}", cwd=source, capture=True).strip()
    if actual != lock["commit"]:
        raise SystemExit(f"Tag does not match locked Chromium commit: {actual}")
    run("git", "checkout", "--detach", actual, cwd=source)

    config = (
        "solutions = " + repr([{
            "name": "src", "url": lock["repository"], "managed": False,
            "custom_deps": {}, "custom_vars": {"checkout_android": True,
                                                "checkout_pgo_profiles": False},
        }]) + "\ntarget_os = ['android']\n"
    )
    config_path = work / ".gclient"
    if config_path.exists() and config_path.read_text() != config:
        raise SystemExit("Existing .gclient differs; choose a separate --work directory.")
    config_path.write_text(config)
    env = build_env(work)
    run("gclient", "sync", "--nohooks", "--no-history", "--shallow",
        f"--jobs={args.jobs}", "--revision", f"src@{lock['commit']}", cwd=work, env=env)
    print(f"Synced Chromium {lock['version']} at {actual}.")


if __name__ == "__main__":
    main()
