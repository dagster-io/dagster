#!/bin/bash
set -euo pipefail

# Environment variables with defaults
export BUILDKITE_FOLDER_GIT_REPO_PATH="${BUILDKITE_FOLDER_GIT_REPO_PATH:-https://github.com/albertfast/dagster.git}"
export BUILDKITE_FOLDER_GIT_REPO_DIR="${BUILDKITE_FOLDER_GIT_REPO_DIR:-/tmp/buildkite-folder}"
export BUILDKITE_FOLDER_GIT_REPO_BRANCH="${BUILDKITE_FOLDER_GIT_REPO_BRANCH:-Issue-31069}"
export DAGSTER_GIT_REPO_DIR="${DAGSTER_GIT_REPO_DIR:-/workspaces/dagster}"

echo "🔧 Setting up .buildkite folder from fallback repo..."
echo "📁 Target directory: $DAGSTER_GIT_REPO_DIR"
echo "🌐 Fallback repo: $BUILDKITE_FOLDER_GIT_REPO_PATH"
echo "📂 Clone destination: $BUILDKITE_FOLDER_GIT_REPO_DIR"
echo "🌿 Branch: $BUILDKITE_FOLDER_GIT_REPO_BRANCH"

# Clone the fallback repo only if not already present
if [ ! -d "$BUILDKITE_FOLDER_GIT_REPO_DIR" ]; then
  echo "📥 Cloning fallback repository..."
  git clone --depth 1 -b "$BUILDKITE_FOLDER_GIT_REPO_BRANCH" "$BUILDKITE_FOLDER_GIT_REPO_PATH" "$BUILDKITE_FOLDER_GIT_REPO_DIR"
else
  echo "✅ Fallback repository already exists locally"
fi

# ✅ Check if .buildkite directory exists in cloned fallback repo
if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite" ]; then
  mkdir -p "$DAGSTER_GIT_REPO_DIR/.buildkite"
  cp -r "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/"* "$DAGSTER_GIT_REPO_DIR/.buildkite/"
  echo "✅ Successfully copied .buildkite folder to DAGSTER repo"
else
  echo "❌ Error: .buildkite directory not found in fallback repo: $BUILDKITE_FOLDER_GIT_REPO_DIR"
  exit 1
fi
