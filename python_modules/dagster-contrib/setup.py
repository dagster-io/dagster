import sys
import os

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


def long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.rst'), 'r') as fh:
        return fh.read()


version = {}
with open("dagster_contrib/version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setup(
    name='dagster_contrib',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description=
    'Utilities and examples for working with dagster, an opinionated framework for expressing data pipelines.',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/dagster-io/dagster',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(
        exclude=[
            'dagster_examples/dagster_examples_tests',
            'pandas/pandas_tests',
            'sqlalchemy_sqlalchemy_tests',
        ]
    ),
    install_requires=[
        'dagster',
        'dagstermill',
    ],
    extras_require={
        'pandas': [
            'pandas>=0.22.0',
            'pyarrow>=0.8.0',
        ],
        'sqlalchemy': [
            'sqlalchemy>=1.2.7',
            'jinja2>=2.8',
        ]
    }
)
