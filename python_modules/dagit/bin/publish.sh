#!/bin/bash

rm -r dist/
cd ./dagit/webapp
yarn install
yarn build
cd ../../
python3 setup.py sdist bdist_wheel
twine upload dist/*
