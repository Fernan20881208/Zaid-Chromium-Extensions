#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zipfile

from common import ROOT, revision, run


def validate_apk(path):
    with zipfile.ZipFile(path) as apk:
        if apk.testzip() is not None:
            raise ValueError("APK ZIP checksum failure")
        names = apk.namelist()
        if "AndroidManifest.xml" not in names:
            raise ValueError("APK has no AndroidManifest.xml")
        libraries = [name for name in names if name.startswith("lib/") and name.endswith(".so")]
        if not libraries or any(not name.startswith("lib/arm64-v8a/") for name in libraries):
            raise ValueError("APK must contain only ARM64 native libraries")
        for name in libraries:
            with apk.open(name) as library:
                header = library.read(20)
            if (len(header) != 20 or header[:6] != b"\x7fELF\x02\x01"
                    or struct.unpack_from("<H", header, 18)[0] != 183):
                raise ValueError(f"Not an AArch64 ELF library: {name}")
    return len(libraries)


def sdk_tools(source):
    candidates = list(source.glob("third_party/android_sdk/**/build-tools/*/apksigner"))
    if not candidates:
        raise FileNotFoundError("Android SDK apksigner missing; run gclient runhooks")
    signer = sorted(candidates, key=lambda p: [int(v) for v in re.findall(r"\d+", p.parent.name)])[-1]
    return signer.parent


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=ROOT / "work")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    source = args.work.resolve() / "src"
    original = source / "out/ZaidArm64/apks/ChromePublic.apk"
    count = validate_apk(original)
    tool_dir = sdk_tools(source)
    lock = revision()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    has_key = bool(os.environ.get("ZAID_KEYSTORE_BASE64"))
    signing = "release" if has_key else "development"
    if os.environ.get("ZAID_REQUIRE_RELEASE_SIGNING") == "1" and not has_key:
        raise SystemExit("Release signing key is required; no release will be published.")
    filename = f"Zaid-Chromium-{lock['version']}-arm64-{signing}.apk"
    destination = output / filename
    with tempfile.TemporaryDirectory(prefix="zaid-sign-") as temporary:
        temp = Path(temporary)
        if has_key:
            required = ("ZAID_KEYSTORE_PASSWORD", "ZAID_KEY_ALIAS", "ZAID_KEY_PASSWORD")
            if not all(os.environ.get(name) for name in required):
                raise SystemExit("All four Android signing secrets are required.")
            key = temp / "release.jks"
            key.write_bytes(base64.b64decode(os.environ["ZAID_KEYSTORE_BASE64"], validate=True))
            key.chmod(0o600)
            aligned = temp / "aligned.apk"
            run(tool_dir / "zipalign", "-P", "16", "-f", "4", original, aligned)
            run(tool_dir / "apksigner", "sign", "--ks", key,
                "--ks-key-alias", os.environ["ZAID_KEY_ALIAS"],
                "--ks-pass", "env:ZAID_KEYSTORE_PASSWORD",
                "--key-pass", "env:ZAID_KEY_PASSWORD", "--out", destination, aligned)
        else:
            shutil.copyfile(original, destination)
    certificate = run(tool_dir / "apksigner", "verify", "--verbose", "--print-certs",
                      destination, capture=True)
    run(tool_dir / "zipalign", "-c", "-P", "16", "4", destination)
    badging = run(tool_dir / "aapt2", "dump", "badging", destination, capture=True)
    if "name='com.zaid.chromium'" not in badging:
        raise ValueError("Unexpected APK package name")
    version = re.search(r"versionName='([^']+)'", badging)
    if not version or not version[1].startswith(lock["version"]):
        raise ValueError("Unexpected Chromium APK version")
    minimum = re.search(r"sdkVersion:'(\d+)'", badging)
    if not minimum or int(minimum[1]) > 36:
        raise ValueError("APK cannot be installed on Android 16 (API 36)")
    (output / "signing-certificate.txt").write_text(certificate)
    (output / "apk-badging.txt").write_text(badging)
    shutil.copyfile(ROOT / "chromium/revision.json", output / "revision.json")
    shutil.copyfile(source / "out/ZaidArm64/args.gn", output / "args.gn")
    fork_commit = run("git", "rev-parse", "HEAD", cwd=ROOT, capture=True).strip()
    metadata = {
        "chromium": lock, "fork_commit": fork_commit, "apk": filename,
        "apk_sha256": digest(destination), "signing": signing,
        "native_library_count": count, "package": "com.zaid.chromium",
        "compiled": True, "android16_device_tested": False,
        "tampermonkey_tested": False, "violentmonkey_tested": False,
        "patches": {p.name: digest(p) for p in sorted((ROOT / "patches").glob("*.patch"))},
    }
    (output / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "release-notes.md").write_text(
        f"Experimental ARM64 build of Zaid Chromium Extensions based on Chromium {lock['version']}.\n\n"
        f"Source commit: {fork_commit}. Signing: {signing}.\n\n"
        "Includes Desktop Android extensions, chrome://extensions, unpacked-folder loading and a native CRX picker. "
        "Chromium verifies CRX signatures and shows its permission prompt.\n\n"
        "Compilation and APK signature/ABI checks passed. Android 16 device testing and Tampermonkey/Violentmonkey compatibility are still unverified.\n"
    )
    deliverables = [destination, output / "build-metadata.json", output / "revision.json", output / "args.gn"]
    (output / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in deliverables))
    print(f"Verified APK: {destination}")


if __name__ == "__main__":
    main()
