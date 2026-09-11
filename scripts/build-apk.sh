#!/usr/bin/env bash
set -e

ROOT=$(pwd)
mkdir -p "$ROOT/work"

cd "$ROOT/work"

echo "[Zaid Chromium] Chromium source checkout stage"
echo "[Zaid Chromium] Apply extension patches stage"
echo "[Zaid Chromium] GN configuration stage"
echo "[Zaid Chromium] Build APK stage"

# Real Chromium compilation will be enabled after depot_tools and source sync are added.
