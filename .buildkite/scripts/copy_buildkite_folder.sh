#!/bin/bash
set -euo pipefail

# This script clones the buildkite folder repository and copies the .buildkite folder to the current repository

# Environment variables
export BUILDKITE_FOLDER_GIT_REPO_PATH="${BUILDKITE_FOLDER_GIT_REPO_PATH:-https://github.com/albertfast/dagster.git}"
export BUILDKITE_FOLDER_GIT_REPO_DIR="${BUILDKITE_FOLDER_GIT_REPO_DIR:-/tmp/buildkite-folder}"
export BUILDKITE_FOLDER_GIT_REPO_BRANCH="${BUILDKITE_FOLDER_GIT_REPO_BRANCH:-master}"
export BUILDKITE_FOLDER_GIT_REPO_SPARSE_CHECKOUT="${BUILDKITE_FOLDER_GIT_REPO_SPARSE_CHECKOUT:-true}"

# Function to clone buildkite folder repository
clone_buildkite_folder_repo() {
  echo "Cloning repo from ${BUILDKITE_FOLDER_GIT_REPO_BRANCH}@HEAD (shallow clone, sparse checkout: .buildkite only)"
  
  # Create the directory if it doesn't exist
  mkdir -p "${BUILDKITE_FOLDER_GIT_REPO_DIR}"
  
  # Initialize a git repository
  cd "${BUILDKITE_FOLDER_GIT_REPO_DIR}"
  git init
  git remote add origin "${BUILDKITE_FOLDER_GIT_REPO_PATH}"
  
  # Set up sparse checkout if enabled
  if [[ "${BUILDKITE_FOLDER_GIT_REPO_SPARSE_CHECKOUT}" == "true" ]]; then
    git config core.sparseCheckout true
    echo ".buildkite" > .git/info/sparse-checkout
  fi
  
  # Fetch and checkout the specified branch
  git fetch --depth=1 origin "${BUILDKITE_FOLDER_GIT_REPO_BRANCH}"
  git checkout "origin/${BUILDKITE_FOLDER_GIT_REPO_BRANCH}" -b "${BUILDKITE_FOLDER_GIT_REPO_BRANCH}"
}

# Function to copy .buildkite folder to target repository
copy_buildkite_folder() {
  echo "Copying .buildkite folder to target repository"
  cp -r "${BUILDKITE_FOLDER_GIT_REPO_DIR}/.buildkite" "${TARGET_REPO_DIR}/"
}

# Main execution
TARGET_REPO_DIR="$PWD"

# Only clone if the directory doesn't exist or is empty
if [ ! -d "${BUILDKITE_FOLDER_GIT_REPO_DIR}/.git" ]; then
  clone_buildkite_folder_repo
else
  echo "Using existing buildkite folder repository at ${BUILDKITE_FOLDER_GIT_REPO_DIR}"
fi

# Copy the .buildkite folder
cd "${TARGET_REPO_DIR}"
copy_buildkite_folder

echo "✅ Successfully set up .buildkite folder"
