#!/usr/bin/env bash
set -euo pipefail

if [[ "${GITHUB_ACTIONS:-}" != true || "${RUNNER_ENVIRONMENT:-}" != github-hosted || "${RUNNER_OS:-}" != Linux ]]; then
  echo 'Keeping installed tools on this host; cleanup is limited to GitHub-hosted Linux runners.'
  exit 0
fi

# Chromium fetches its own Android SDK. These image tools are unused by this job.
for zaid_tool_dir in /usr/local/lib/android /usr/share/dotnet /opt/ghc /usr/local/.ghcup /usr/share/swift; do
  if [[ -d "$zaid_tool_dir" && ! -L "$zaid_tool_dir" ]]; then
    sudo -n rm -rf -- "$zaid_tool_dir"
  fi
done
df -h "$GITHUB_WORKSPACE"
