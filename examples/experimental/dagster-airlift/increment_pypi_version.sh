#!/bin/bash

# Define the path to the setup.py file
SETUP_PY_FILE="setup.py"

# Check if setup.py exists
if [ ! -f "$SETUP_PY_FILE" ]; then
    echo "Error: $SETUP_PY_FILE not found!"
    exit 1
fi

# Extract the current version from 'version="x.y.z",'
CURRENT_VERSION=$(sed -n 's/.*version="\([0-9]*\.[0-9]*\.[0-9]*\)",.*/\1/p' "$SETUP_PY_FILE")
if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Version string not found in $SETUP_PY_FILE!"
    exit 1
fi

echo "Current version: $CURRENT_VERSION"

# Extract x, y, z components of the version
IFS='.' read -r X Y Z <<< "$CURRENT_VERSION"

# Increment z
NEW_Z=$((Z + 1))
NEW_VERSION="$X.$Y.$NEW_Z"
echo "New version: $NEW_VERSION"

# Create a backup of the original file
cp "$SETUP_PY_FILE" "${SETUP_PY_FILE}.bak"

# Replace the old version with the new version in setup.py
echo "Updating version in $SETUP_PY_FILE..."
sed -i "" "s|version=\"$CURRENT_VERSION\"|version=\"$NEW_VERSION\"|" "$SETUP_PY_FILE"

# Run the specified commands
echo "Running commands..."
if ! ./build_and_publish.sh; then
    echo "Commands failed. Reverting to original version..."
    mv "${SETUP_PY_FILE}.bak" "$SETUP_PY_FILE"
    exit 1
fi

# Clean up the backup if successful
rm "${SETUP_PY_FILE}.bak"
echo "Commands completed successfully. Version updated to $NEW_VERSION."
