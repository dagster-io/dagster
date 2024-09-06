#!/bin/bash
# There's a lot of shared work here with the `update_mirror` step of the OSS release process.
# Code here can be consolidated.

# Exit immediately if a command exits with a non-zero status
set -e

# Create a new temporary directory
temp_dir=$(mktemp -d)
echo "Created temporary directory: $temp_dir"

# Change to the temporary directory
cd "$temp_dir"

# Initialize git, add remote, fetch, and reset
echo "Initializing git repository..."
git init
echo "Adding remote..."
git remote add origin git@github.com:dagster-io/airlift-tutorial.git
echo "Fetching and resetting..."
git fetch origin
git reset --soft origin/main

# Go back to the original directory
cd -

echo "Copying files to temporary directory..."
# Copy files from examples/tutorial_examples to the temporary directory
rsync -av \
    --exclude='.git' \
    --exclude='.airflow_home' \
    --exclude='.dagster_home' \
    --exclude='*.egg-info' \
    --exclude='tutorial_example_tests' \
    --exclude='conftest.py' \
    examples/tutorial-example/ "$temp_dir/"

# Make the version extraction script executable
chmod +x "scripts/extract_pypi_version.sh"
# Get the version number
version=$(./scripts/extract_pypi_version.sh)

# Change to the temporary directory again
cd "$temp_dir"

# Add all files to git
git add .


echo "Committing with version $version..."
# Commit message is the version number
git commit -m "$version" --allow-empty

echo "Pushing to origin..."
# Push to origin
git push origin HEAD --force

echo "Pushed successfully. Cleaning up..."
# Clean up: remove the temporary directory
cd ..
rm -rf "$temp_dir"

echo "Script completed successfully"