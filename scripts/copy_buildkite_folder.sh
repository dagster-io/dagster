#!/bin/bash
set -euo pipefail

# Script to restore the .buildkite folder to the current repository
# Usage: ./copy_buildkite_folder.sh

echo "🔧 Setting up .buildkite folder from buildkite folder repository..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Repository root: $REPO_ROOT"

# Parse BUILDKITE_FOLDER_BRANCH from BUILDKITE_MESSAGE if available
if [ -n "${BUILDKITE_MESSAGE:-}" ]; then
    # Extract BUILDKITE_FOLDER_BRANCH=value from BUILDKITE_MESSAGE (match everything up to closing bracket)
    GREP_RESULT=$(echo "$BUILDKITE_MESSAGE" | grep -o "BUILDKITE_FOLDER_BRANCH=[^]]*" || echo "")
    PARSED_BRANCH=$(echo "$GREP_RESULT" | cut -d= -f2 || echo "")
    
    if [ -n "$PARSED_BRANCH" ]; then
        export BUILDKITE_FOLDER_BRANCH="$PARSED_BRANCH"
    fi
fi

export BUILDKITE_FOLDER_BRANCH="${BUILDKITE_FOLDER_BRANCH:-master}"
export COMMIT_HASH="${COMMIT_HASH:-HEAD}"

if [[ "$BUILDKITE_FOLDER_BRANCH" != "master" && "$COMMIT_HASH" == "HEAD" ]]; then
  RESOLVED=$(git ls-remote $BUILDKITE_FOLDER_GIT_REPO_PATH "refs/heads/$BUILDKITE_FOLDER_BRANCH" | awk '{ print $1 }')
  if [[ -z "$RESOLVED" ]]; then
    echo "Error: Branch $INTERNAL_BRANCH not found in remote repository"
    exit 1
  fi
  COMMIT_HASH=$RESOLVED
fi

export BUILDKITE_FOLDER_GIT_REPO_DIR="${BUILDKITE_FOLDER_GIT_REPO_DIR:-$(cd ../; pwd)/buildkite-folder}"
echo "BUILDKITE_FOLDER_GIT_REPO_DIR = $BUILDKITE_FOLDER_GIT_REPO_DIR"

# Clean up any existing directory first
if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR" ]; then
    echo "Cleaning up existing directory: $BUILDKITE_FOLDER_GIT_REPO_DIR"
    rm -rf "$BUILDKITE_FOLDER_GIT_REPO_DIR"
fi

echo "Cloning repo from $BUILDKITE_FOLDER_BRANCH@$COMMIT_HASH (shallow clone, sparse checkout: .buildkite only)"

# Clone the buildkite folder repo with sparse checkout
if [ -z "${PYTEST_CURRENT_TEST:-}" ]; then
  git clone --depth=1 --filter=blob:none --no-checkout $BUILDKITE_FOLDER_GIT_REPO_PATH $BUILDKITE_FOLDER_GIT_REPO_DIR -b $BUILDKITE_FOLDER_BRANCH
  pushd $BUILDKITE_FOLDER_GIT_REPO_DIR
  
  # Setup sparse-checkout to only include .buildkite folder
  git sparse-checkout init --cone
  git sparse-checkout set .buildkite
  
  git checkout $COMMIT_HASH
  popd
fi

# Copy .buildkite folder from buildkite folder repo
if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite" ]; then
    echo "Copying .buildkite folder from buildkite folder repo..."
    
    # Create .buildkite directory if it doesn't exist
    mkdir -p "$REPO_ROOT/.buildkite"
    
    # Copy specific subdirectories
    if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/dagster-buildkite" ]; then
        cp -r "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/dagster-buildkite" "$REPO_ROOT/.buildkite/"
        echo "Copied dagster-buildkite"
    fi
    
    if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/hooks" ]; then
        cp -r "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/hooks" "$REPO_ROOT/.buildkite/"
        echo "Copied hooks"
    fi
    
    if [ -d "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/scripts" ]; then
        cp -r "$BUILDKITE_FOLDER_GIT_REPO_DIR/.buildkite/scripts" "$REPO_ROOT/.buildkite/"
        echo "Copied scripts"
    fi
    
    echo "Successfully copied .buildkite folder to current repository"
else
    echo "Error: .buildkite folder not found in buildkite folder repository"
    exit 1
fi

# Clean up - remove cloned buildkite folder repo
echo "Cleaning up cloned buildkite folder repo..."
rm -rf "$BUILDKITE_FOLDER_GIT_REPO_DIR"

echo "✅ .buildkite folder setup complete"