PACKAGE_TO_RELEASE_PATH=$(buildkite-agent meta-data get package-to-release-path)
VERSION_TO_RELEASE=$(buildkite-agent meta-data get version-to-release)

if [ -z "$PACKAGE_TO_RELEASE_PATH" ]; then
    echo "Please provide the path to the package to release."
    exit 1
fi
if [ -z "$VERSION_TO_RELEASE" ]; then
    echo "Please provide the version to release."
    exit 1
fi

mkdir -p package_prerelease
cp -R $PACKAGE_TO_RELEASE_PATH/* package_prerelease
pushd package_prerelease

# Update both a hardcoded version, if set, in setup.py, and
# find where __version__ is set and update it
sed -i "" "s|return \"1!0+dev\"|return \"$VERSION_TO_RELEASE\"|" setup.py
grep -rl "__version__ = \"1!0+dev\"" ./ | xargs sed -i "" "s|\"1!0+dev\"|\"$VERSION_TO_RELEASE\"|"

echo "Building package..."
python3 -m build
echo "Uploading to pypi..."
# Capture the output of the twine upload command
python3 -m twine upload --username "__token__" --password $PYPI_TOKEN --repository pypi dist/* --verbose
