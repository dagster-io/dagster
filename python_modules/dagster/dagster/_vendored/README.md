# Dagster Vendored libraries

This package contains open-source dependencies that we have copied into the Dagster code-base ("vendored") rather than added as a dependency in the setup.py in the traditional fashion.

A package could be a good candidate for vendoring if it is relatively small and self-contained (so it won't bloat the package size), and/or supporting the full set of versions of the package that users might have installed is hard without introducing onerous or disruptive pins.

Currently vendored packages:

- dateutil is vendored at the 2.9.0post0 release: https://pypi.org/project/python-dateutil/2.9.0.post0/ due to being frequently imported from two different pypi packages, https://pypi.org/project/python-dateutil/ and https://pypi.org/project/py-dateutil/, sometimes simultaneously (including in the default AWS EMR python environment as of June 2024)
- croniter is vendored at the 6.0.0 release: https://pypi.org/project/croniter/6.0.0/ due to the author planning to remove it from PyPI.

To vendor a package:

- Copy the source package at the tag you're using into this folder
- Add the LICENSE file of the vendored package
- Replace any absolute imports with relative imports
- Replace any imports of the vendored package within the dagster package to point to the \_vendored package
- If you make any changes from the vendored code (for example, replacing absolute imports with relative imports so that they correctly use the vendored package), clearly indicate the changes in comments like this, in case we need to upgrade the vendored package version in the future:

```
# CHANGED IN VENDORED VERSION
```
