PACKAGE_TO_RELEASE_PATH=$(buildkite-agent meta-data get package-to-release-path)
VERSION_TO_RELEASE=$(buildkite-agent meta-data get version-to-release --default '')

if [ -z "$PACKAGE_TO_RELEASE_PATH" ]; then
    echo "Please provide the path to the package to release."
    exit 1
fi
if [ -z "$VERSION_TO_RELEASE" ]; then
    echo "Inferring version to release from package."
    EXISTING_VERSION=$(grep 'version=' $PACKAGE_TO_RELEASE_PATH/setup.py)
    echo "Existing version: $EXISTING_VERSION"
    MAJOR_VAR=$(echo $EXISTING_VERSION | sed -E 's/.*version=[^0-9]([0-9].+)([0-9]+).*/\1/')
    MINOR_VAR=$(echo $EXISTING_VERSION | sed -E 's/.*version=[^0-9]([0-9].+)([0-9]+).*/\2/')
    INCREMENTED_MINOR_VAR=$((MINOR_VAR + 1))

    VERSION_TO_RELEASE="$MAJOR_VAR$INCREMENTED_MINOR_VAR"

    echo "Going to release version $VERSION_TO_RELEASE"
fi

# # Update both a hardcoded version, if set, in setup.py, and
# # find where __version__ is set and update it
# sed -i "s|version=\".*\"|version=\"$VERSION_TO_RELEASE\"|" "$PACKAGE_TO_RELEASE_PATH/setup.py"
# grep -rl "__version__ = \".*\"" "$PACKAGE_TO_RELEASE_PATH" | xargs sed -i "s|__version__ = \".*\"|__version__ = \"$VERSION_TO_RELEASE\"|"

# mkdir -p package_prerelease
# cp -R $PACKAGE_TO_RELEASE_PATH/* package_prerelease
# cd package_prerelease

# echo "Building package..."
# python3 -m build
# echo "Uploading to pypi..."
# # Capture the output of the twine upload command
# python3 -m twine upload --username "__token__" --password "$PYPI_TOKEN" --repository pypi dist/* --verbose
