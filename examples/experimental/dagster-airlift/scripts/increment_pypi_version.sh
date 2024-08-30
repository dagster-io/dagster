#!/bin/bash

# Get the current version using the extract_pypi_version.sh script
CURRENT_VERSION=$(./scripts/extract_pypi_version.sh)
if [ $? -ne 0 ]; then
    echo "Error getting current version"
    exit 1
fi

echo "Current version: $CURRENT_VERSION"

# Extract x, y, z components of the version
IFS='.' read -r X Y Z <<< "$CURRENT_VERSION"

# Increment z
NEW_Z=$((Z + 1))
NEW_VERSION="$X.$Y.$NEW_Z"
echo "New version: $NEW_VERSION"

# Define the path to the setup.py file
SETUP_PY_FILE="setup.py"

# Create a backup of the original file
cp "$SETUP_PY_FILE" "${SETUP_PY_FILE}.bak"

# Replace the old version with the new version in setup.py
echo "Updating version in $SETUP_PY_FILE..."
sed -i "" "s|version=\"$CURRENT_VERSION\"|version=\"$NEW_VERSION\"|" "$SETUP_PY_FILE"

# Run the specified commands
echo "Running commands..."
if ! ./scripts/build_and_publish.sh; then
    echo "Commands failed. Reverting to original version..."
    mv "${SETUP_PY_FILE}.bak" "$SETUP_PY_FILE"
    exit 1
fi

# Clean up the backup if successful
rm "${SETUP_PY_FILE}.bak"
echo "Commands completed successfully. Version updated to $NEW_VERSION."