#!/bin/bash
set -euo pipefail

# This script clones the buildkite folder repository and copies the .buildkite folder to the current repository

# Environment variables with defaults
export BUILDKITE_FOLDER_GIT_REPO_PATH="${BUILDKITE_FOLDER_GIT_REPO_PATH:-https://github.com/albertfast/dagster.git}"
export BUILDKITE_FOLDER_GIT_REPO_DIR="${BUILDKITE_FOLDER_GIT_REPO_DIR:-/tmp/buildkite-folder}"
export BUILDKITE_FOLDER_GIT_REPO_BRANCH="${BUILDKITE_FOLDER_GIT_REPO_BRANCH:-issue-31069}"
export DAGSTER_GIT_REPO_DIR="${DAGSTER_GIT_REPO_DIR:-/workspaces/dagster}"

echo "🔧 Setting up .buildkite folder from buildkite folder repository..."
echo "Repository root: $DAGSTER_GIT_REPO_DIR"
echo "BUILDKITE_FOLDER_GIT_REPO_PATH = $BUILDKITE_FOLDER_GIT_REPO_PATH"
echo "BUILDKITE_FOLDER_GIT_REPO_DIR = $BUILDKITE_FOLDER_GIT_REPO_DIR"
echo "BUILDKITE_FOLDER_GIT_REPO_BRANCH = $BUILDKITE_FOLDER_GIT_REPO_BRANCH"

# Clone the buildkite folder repository if it doesn't exist
if [ ! -d "$BUILDKITE_FOLDER_GIT_REPO_DIR" ]; then
  mkdir -p "$BUILDKITE_FOLDER_GIT_REPO_DIR"
  git clone --depth 1 -b "$BUILDKITE_FOLDER_GIT_REPO_BRANCH" "$BUILDKITE_FOLDER_GIT_REPO_PATH" "$BUILDKITE_FOLDER_GIT_REPO_DIR"
fi

# Copy the .buildkite folder to the current repository
mkdir -p "$DAGSTER_GIT_REPO_DIR/.buildkite"
cp -r "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite"/* "$DAGSTER_GIT_REPO_DIR/.buildkite/"

echo "✅ Successfully set up .buildkite folder"
