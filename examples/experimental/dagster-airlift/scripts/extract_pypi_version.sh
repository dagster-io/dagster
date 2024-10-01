#!/bin/bash

# Define the path to the setup.py file
SETUP_PY_FILE="setup.py"

# Check if setup.py exists
if [ ! -f "$SETUP_PY_FILE" ]; then
    echo "Error: $SETUP_PY_FILE not found!" >&2
    exit 1
fi

# Extract the current version from 'version="x.y.z",'
CURRENT_VERSION=$(sed -n 's/.*version="\([0-9]*\.[0-9]*\.[0-9]*\)",.*/\1/p' "$SETUP_PY_FILE")
if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Version string not found in $SETUP_PY_FILE!" >&2
    exit 1
fi

# Output the current version
echo "$CURRENT_VERSION"