# This is a component-specific version of build_and_publish.sh
# It is used to release dagster-components and dagster-dg at the same time

VERSION_TO_RELEASE=$(buildkite-agent meta-data get version-to-release --default '')

git checkout $BUILDKITE_BRANCH



if [ -z "$VERSION_TO_RELEASE" ]; then
    echo "Package does not have a fixed version in setup.py, please provide release candidate version to release."
    exit 1
fi


# Update both a hardcoded version, if set, in setup.py, and
# find where __version__ is set and update it
echo "Updating version in source..."
sed -i "s|version=\".*\"|version=\"$VERSION_TO_RELEASE\"|" "python_modules/libraries/dagster-components/setup.py"
sed -i "s|version=\".*\"|version=\"$VERSION_TO_RELEASE\"|" "python_modules/libraries/dagster-dg/setup.py"
grep -rl "__version__ = \".*\"" "python_modules/libraries/dagster-components" | xargs sed -i "s|__version__ = \".*\"|__version__ = \"$VERSION_TO_RELEASE\"|"
grep -rl "__version__ = \".*\"" "python_modules/libraries/dagster-dg" | xargs sed -i "s|__version__ = \".*\"|__version__ = \"$VERSION_TO_RELEASE\"|"


# Release dagster-components
mkdir -p package_prerelease
cp -R python_modules/libraries/dagster-components/* package_prerelease
cd package_prerelease

echo "Building package..."
python3 -m build

echo "Uploading to pypi..."
python3 -m twine upload --username "__token__" --password "$PYPI_TOKEN" --repository pypi dist/* --verbose

cd ..
rm -rf package_prerelease


# Release dagster-dg
mkdir -p package_prerelease
cp -R python_modules/libraries/dagster-dg/* package_prerelease
cd package_prerelease

echo "Building package..."
python3 -m build

echo "Uploading to pypi..."
python3 -m twine upload --username "__token__" --password "$PYPI_TOKEN" --repository pypi dist/* --verbose

cd ..
rm -rf package_prerelease


echo "Committing and tagging release..."
git add -A
git config --global user.email "devtools@dagsterlabs.com"
git config --global user.name "Dagster Labs"
git commit -m "dagster-dg $VERSION_TO_RELEASE"

git tag "dagster-dg/v$VERSION_TO_RELEASE"
git push origin "dagster-dg/v$VERSION_TO_RELEASE"
git tag "dagster-components/v$VERSION_TO_RELEASE"
git push origin "dagster-components/v$VERSION_TO_RELEASE"
