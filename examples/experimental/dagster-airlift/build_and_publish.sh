# How to release:
# 1. increment the version number in pyproject.toml
# 2. ensure you have an API key from the elementl PyPI account (account is in the password manager)
# 3. run this script from this directory
# 4. once propted, use '__token__' for the username and the API key for the password

rm -rf dist/*
rm -rf dagster_airlift_prerelease/dagster_airlift_patched
cp -R dagster_airlift dagster_airlift_prerelease/dagster_airlift_patched
echo "Patching dagster_airlift"
python3 -m build
echo "Building dagster_airlift"
python3 -m twine upload --repository pypi dist/* --verbose

# cleanup
rm -rf dist/*
rm -rf dagster_airlift_prerelease/dagster_airlift_patched