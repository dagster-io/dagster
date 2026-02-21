# Use gsed on macOS (BSD sed has different -i behavior)
if [[ "$(uname)" == "Darwin" ]]; then
    if command -v gsed &> /dev/null; then
        SED="gsed"
    else
        echo "Error: gsed is required on macOS but was not found."
        echo "Install it with: brew install gnu-sed"
        exit 1
    fi
else
    SED="sed"
fi

PACKAGE_TO_RELEASE_PATH=$(buildkite-agent meta-data get package-to-release-path)
VERSION_TO_RELEASE=$(buildkite-agent meta-data get version-to-release --default '')

git checkout $BUILDKITE_BRANCH

if [ -z "$PACKAGE_TO_RELEASE_PATH" ]; then
    echo "Please provide the path to the package to release."
    exit 1
fi

# Detect package type
if [ -f "$PACKAGE_TO_RELEASE_PATH/pyproject.toml" ]; then
    PACKAGE_TYPE="pyproject"
elif [ -f "$PACKAGE_TO_RELEASE_PATH/setup.py" ]; then
    PACKAGE_TYPE="setup_py"
else
    echo "No pyproject.toml or setup.py found in $PACKAGE_TO_RELEASE_PATH"
    exit 1
fi

echo "Detected package type: $PACKAGE_TYPE"

# Determine if package has a fixed version and extract version info
if [ "$PACKAGE_TYPE" = "pyproject" ]; then
    EXISTING_VERSION=$(grep '^version = ' "$PACKAGE_TO_RELEASE_PATH/pyproject.toml" | head -1)
    HAS_FIXED_VERSION=0
    if [[ $EXISTING_VERSION == *"\""* ]]; then
        HAS_FIXED_VERSION=1
    fi
else
    EXISTING_VERSION=$(grep 'version=' $PACKAGE_TO_RELEASE_PATH/setup.py)
    HAS_FIXED_VERSION=0
    if [[ $EXISTING_VERSION == *"\""* ]]; then
        HAS_FIXED_VERSION=1
    fi
fi

if [ -z "$VERSION_TO_RELEASE" ]; then
    if [ $HAS_FIXED_VERSION -eq 0 ]; then
        echo "Package does not have a fixed version, please provide release candidate version to release."
        exit 1
    fi
    echo "Inferring version to release from package."

    if [ "$PACKAGE_TYPE" = "pyproject" ]; then
        # Extract version from pyproject.toml: version = "X.Y.Z"
        EXISTING_VERSION=$(grep '^version = ' "$PACKAGE_TO_RELEASE_PATH/pyproject.toml" | head -1)
        echo "Existing version: $EXISTING_VERSION"
        # Parse version like: version = "1.9.2" -> extract 1.9. and 2
        # For pyproject.toml packages with dev versions, VERSION_TO_RELEASE must be provided
        if [[ -z "$VERSION_TO_RELEASE" && "$EXISTING_VERSION" == *"!0+dev"* ]]; then
            echo "Error: VERSION_TO_RELEASE must be provided for pyproject.toml packages with development versions"
            exit 1
        fi
        MAJOR_VAR=$(echo $EXISTING_VERSION | $SED -E 's/.*version = "([0-9]+\.[0-9]+\.)([0-9]+)".*/\1/')
        MINOR_VAR=$(echo $EXISTING_VERSION | $SED -E 's/.*version = "([0-9]+\.[0-9]+\.)([0-9]+)".*/\2/')
    else
        EXISTING_VERSION=$(grep 'version=' $PACKAGE_TO_RELEASE_PATH/setup.py)
        echo "Existing version: $EXISTING_VERSION"
        MAJOR_VAR=$(echo $EXISTING_VERSION | $SED -E 's/.*version=[^0-9]([0-9].+)([0-9]+).*/\1/')
        MINOR_VAR=$(echo $EXISTING_VERSION | $SED -E 's/.*version=[^0-9]([0-9].+)([0-9]+).*/\2/')
    fi

    INCREMENTED_MINOR_VAR=$((MINOR_VAR + 1))
    VERSION_TO_RELEASE="$MAJOR_VAR$INCREMENTED_MINOR_VAR"

    echo "Going to release version $VERSION_TO_RELEASE"
fi

if [ $HAS_FIXED_VERSION -eq 0 ] && [[ $VERSION_TO_RELEASE != *"rc"* ]] && [[ $VERSION_TO_RELEASE != *"post"* ]]; then
    echo "Since this package is published weekly, you must provide a release candidate version to release."
    exit 1
fi


# Update version in source files
echo "Updating version in source..."
if [ "$PACKAGE_TYPE" = "pyproject" ]; then
    # Update version in pyproject.toml and replace 1!0+dev pins with release version
    $SED -i "s|^version = \".*\"|version = \"$VERSION_TO_RELEASE\"|" "$PACKAGE_TO_RELEASE_PATH/pyproject.toml"
    $SED -i "s|==1!0+dev|==$VERSION_TO_RELEASE|g" "$PACKAGE_TO_RELEASE_PATH/pyproject.toml"
else
    # Update hardcoded version in setup.py
    $SED -i "s|version=\".*\"|version=\"$VERSION_TO_RELEASE\"|" "$PACKAGE_TO_RELEASE_PATH/setup.py"
fi

# Update __version__ in Python source files (common to both package types)
grep -rl "__version__ = \".*\"" "$PACKAGE_TO_RELEASE_PATH" | xargs $SED -i "s|__version__ = \".*\"|__version__ = \"$VERSION_TO_RELEASE\"|"

mkdir -p package_prerelease
cp -R $PACKAGE_TO_RELEASE_PATH/* package_prerelease
cd package_prerelease

echo "Building package..."
python3 -m build

echo "Uploading to pypi..."
python3 -m twine upload --username "__token__" --password "$PYPI_TOKEN" --repository pypi dist/* --verbose

cd ..
rm -rf package_prerelease

echo "Committing and tagging release..."
PACKAGE_NAME=$(echo $PACKAGE_TO_RELEASE_PATH | awk -F/ '{print $NF}')
git add -A
git config --global user.email "devtools@dagsterlabs.com"
git config --global user.name "Dagster Labs"
git commit -m "$PACKAGE_NAME $VERSION_TO_RELEASE"

git tag "$PACKAGE_NAME/v$VERSION_TO_RELEASE"
git push origin "$PACKAGE_NAME/v$VERSION_TO_RELEASE"

# only push to branch if there is a fixed version
if [ $HAS_FIXED_VERSION -eq 1 ]; then
    git push origin $BUILDKITE_BRANCH
    exit 0
fi
