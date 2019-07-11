#!/bin/bash

echo -e "[distutils]" >> ~/.pypirc
echo -e "index-servers =" >> ~/.pypirc
echo -e "  pypi" >> ~/.pypirc
echo -e "" >> ~/.pypirc
echo -e "[pypi]" >> ~/.pypirc
echo -e "repository: https://upload.pypi.org/legacy/" >> ~/.pypirc
echo -e "username: $PYPI_USERNAME" >> ~/.pypirc
echo -e "password: $PYPI_PASSWORD" >> ~/.pypirc