# How to release:
# 2. ensure you have an API key from the elementl PyPI account (account is in the password manager)
# 3. run make adhoc_pypi from the root of the dagster-airlift directory
# 4. once propted, use '__token__' for the username and the API key for the password

# Define the path to the .pypirc file
PYPIRC_FILE="$HOME/.pypirc"

# Define cleanup function
cleanup() {
    echo "Cleaning up..."
    rm -rf dist/*
    rm -rf dagster_airlift_prerelease/dagster_airlift_patched
}

# Set trap to call cleanup function on script exit
trap cleanup EXIT

# Check if the .pypirc file exists
if [ ! -f "$PYPIRC_FILE" ]; then
    echo ".pypirc file not found in $HOME."

    # Prompt the user for the API token
    read -p "Enter your API token (must start with 'pypi-'): " API_TOKEN

    # Check if the API token starts with 'pypi-'
    if [[ $API_TOKEN != pypi-* ]]; then
        echo "Invalid API token. It must start with 'pypi-'."
        exit 1
    fi

    # Create the .pypirc file and write the configuration
    cat <<EOF > "$PYPIRC_FILE"
[pypi]
username = __token__
password = $API_TOKEN
EOF

    echo ".pypirc file created successfully."
else
    echo ".pypirc file already exists in $HOME. Using that as pypi credentials."
fi

rm -rf dist/*
rm -rf dagster_airlift_prerelease/dagster_airlift_patched
mkdir -p dagster_airlift_prerelease/dagster_airlift_patched
cp -R dagster_airlift dagster_airlift_prerelease/dagster_airlift_patched
echo "Building package..."
python3 -m build
echo "Uploading to pypi..."
# Capture the output of the twine upload command
TWINE_OUTPUT=$(python3 -m twine upload --repository pypi dist/* --verbose 2>&1)
TWINE_EXIT_CODE=$?

# Check if the output contains a 400 error
if echo "$TWINE_OUTPUT" | grep -q "400 Bad Request"; then
    echo "Error: Twine upload failed with a 400 Bad Request error."
    echo "Twine output:"
    echo "$TWINE_OUTPUT"
    exit 1
elif [ $TWINE_EXIT_CODE -ne 0 ]; then
    echo "Error: Twine upload failed with exit code $TWINE_EXIT_CODE."
    echo "Twine output:"
    echo "$TWINE_OUTPUT"
    exit $TWINE_EXIT_CODE
fi

echo "Upload successful."