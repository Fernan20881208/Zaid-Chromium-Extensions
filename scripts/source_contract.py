#!/usr/bin/env python3
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import tempfile

from apply_patches import apply, series
from common import ROOT, download, revision, run


def check_file(path, content, contract):
    actual = hashlib.sha256(content).hexdigest()
    if actual != contract["sha256"]:
        raise ValueError(f"Pinned source differs: {path} ({actual})")
    for text in contract["contains"]:
        if text not in content.decode():
            raise ValueError(f"Missing upstream integration in {path}: {text}")
    return actual


def fetch_file(path, commit):
    url = f"https://chromium.googlesource.com/chromium/src/+/{commit}/{path}?format=TEXT"
    return base64.b64decode(download(url), validate=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist/source-check.json")
    parser.add_argument("--local-source", type=Path, help="Use an existing pristine subset instead of downloading it")
    args = parser.parse_args()
    lock = revision()
    contracts = json.loads((ROOT / "chromium/source-contract.json").read_text())
    if not args.local_source:
        url = f"https://chromium.googlesource.com/chromium/src/+/refs/tags/{lock['version']}?format=JSON"
        upstream = json.loads(download(url).decode().removeprefix(")]}'\n"))
        if upstream["commit"] != lock["commit"]:
            raise ValueError("Stable tag moved away from pinned commit")
    with tempfile.TemporaryDirectory(prefix="zaid-source-check-") as temporary:
        source = Path(temporary)
        def load(path):
            content = ((args.local_source / path).read_bytes() if args.local_source
                       else fetch_file(path, lock["commit"]))
            digest = check_file(path, content, contracts[path])
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            return path, digest
        with ThreadPoolExecutor(max_workers=6) as pool:
            hashes = dict(pool.map(load, contracts))
        run("git", "init", "-q", source)
        run("git", "add", ".", cwd=source)
        apply(source)
        build_file = (source / "chrome/browser/ui/webui/extensions/BUILD.gn").read_text()
        ui_file = (source / "chrome/browser/ui/webui/extensions/extensions_ui.cc").read_text()
        for name in ("zaid_crx_install_handler.cc", "zaid_crx_install_handler.h"):
            if name not in build_file or not (source / "chrome/browser/ui/webui/extensions" / name).is_file():
                raise ValueError(f"Overlay not connected to GN: {name}")
        if "std::make_unique<ZaidCrxInstallHandler>()" not in ui_file:
            raise ValueError("CRX handler is not registered with the WebUI")
        # The complete series must be safe to rerun after an interrupted build.
        apply(source)
        run("git", "diff", "--check", cwd=source)
    report = {
        "chromium_version": lock["version"], "chromium_commit": lock["commit"],
        "source_hashes": hashes, "patches_applied": [p.name for p in series()],
        "idempotent": True, "overlay_connected": True,
        "validation": "source hashes, required upstream integration, patch applicability",
        "compiled": False, "device_tested": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Validated {len(hashes)} upstream files and {len(series())} patches. Compilation was not performed.")


if __name__ == "__main__":
    main()
