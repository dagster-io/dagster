# How to release:
# 1. increment the version number in pyproject.toml
# 2. ensure you have an API key from the elementl PyPI account (account is in the password manager)
# 3. run this script from this directory
# 4. once propted, use '__token__' for the username and the API key for the password

# Define the path to the .pypirc file
PYPIRC_FILE="$HOME/.pypirc"

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
cp -R dagster_airlift dagster_airlift_prerelease/dagster_airlift_patched
echo "Building package..."
python3 -m build
echo "Uploading to pypi..."
python3 -m twine upload --repository pypi dist/* --verbose

# cleanup
echo "Cleaning up..."
rm -rf dist/*
rm -rf dagster_airlift_prerelease/dagster_airlift_patched