#!/bin/bash
set -euo pipefail

# Environment variables with defaults
: "${BUILDKITE_FOLDER_GIT_REPO_PATH:=https://github.com/albertfast/buildkite-folder.git}"
export BUILDKITE_FOLDER_GIT_REPO_PATH

: "${BUILDKITE_FOLDER_GIT_REPO_DIR:=/tmp/buildkite-folder}"
export BUILDKITE_FOLDER_GIT_REPO_DIR

: "${BUILDKITE_FOLDER_BRANCH:=master}"
export BUILDKITE_FOLDER_BRANCH

: "${COMMIT_HASH:=HEAD}"
export COMMIT_HASH

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "🔧 Setting up .buildkite folder from: $BUILDKITE_FOLDER_GIT_REPO_PATH"
echo "Repo root: $REPO_ROOT"
echo "Branch: $BUILDKITE_FOLDER_BRANCH"
echo "Commit: $COMMIT_HASH"

# Cleanup existing
rm -rf "$BUILDKITE_FOLDER_GIT_REPO_DIR"
mkdir -p "$BUILDKITE_FOLDER_GIT_REPO_DIR"

# Clone (sparse)
git clone --depth=1 --filter=blob:none --no-checkout "$BUILDKITE_FOLDER_GIT_REPO_PATH" "$BUILDKITE_FOLDER_GIT_REPO_DIR" -b "$BUILDKITE_FOLDER_BRANCH"
pushd "$BUILDKITE_FOLDER_GIT_REPO_DIR"
git sparse-checkout init --cone
git sparse-checkout set .buildkite
git checkout "$COMMIT_HASH"
popd

# Copy .buildkite folder
if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite" ]; then
    mkdir -p "$REPO_ROOT/.buildkite"
    cp -r "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/"* "$REPO_ROOT/.buildkite/"
    echo "✅ Copied .buildkite folder successfully"
else
    echo "❌ Error: .buildkite directory not found in cloned repo"
    exit 1
fi

# Cleanup clone
rm -rf "$BUILDKITE_FOLDER_GIT_REPO_DIR"
