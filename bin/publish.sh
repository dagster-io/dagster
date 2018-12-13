#!/bin/bash

# dagster
pushd python_modules/dagster/
rm -r dist/
python3 setup.py sdist bdist_wheel
twine upload dist/*
popd

# dagit
pushd python_modules/dagit/
rm -r dist/
cd ./dagit/webapp
yarn install
yarn build
cd ../../
python3 setup.py sdist bdist_wheel
twine upload dist/*
popd

# dagstermill
pushd python_modules/dagstermill/
rm -r dist/
python3 setup.py sdist bdist_wheel
twine upload dist/*
popd
