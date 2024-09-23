PACKAGE_TO_RELEASE_PATH=$(buildkite-agent meta-data get package-to-release-path)
VERSION_TO_RELEASE=$(buildkite-agent meta-data get version-to-release --default '')

git checkout $BUILDKITE_BRANCH

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

# Update both a hardcoded version, if set, in setup.py, and
# find where __version__ is set and update it
echo "Updating version in source..."
sed -i "s|version=\".*\"|version=\"$VERSION_TO_RELEASE\"|" "$PACKAGE_TO_RELEASE_PATH/setup.py"
grep -rl "__version__ = \".*\"" "$PACKAGE_TO_RELEASE_PATH" | xargs sed -i "s|__version__ = \".*\"|__version__ = \"$VERSION_TO_RELEASE\"|"

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
git push origin $BUILDKITE_BRANCH
