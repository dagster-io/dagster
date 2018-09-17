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
with open("dagster/version.py") as fp:
    exec(fp.read(), version) # pylint: disable=W0122

setup(
    name='dagster',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description='Dagster is an opinionated programming model for data pipelines.',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/dagster-io/dagster',
    classifiers=(
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ),
    packages=find_packages(exclude=['dagster_tests']),
    install_requires=[
        # standard python 2/3 compatability things
        'enum34>=1.1.6',
        'future>=0.16.0',
        'funcsigs>=1.0.2',

        # cli
        'click>=6.7',
        'coloredlogs>=10.0',
        'graphviz>=0.8.3',
        'pyyaml>=3.12',

        # core (not explicitly expressed atm)
        'six>=1.11.0',
        'toposort>=1.5',

        # pandas kernel
        'pandas>=0.22.0',
        'pyarrow>=0.8.0',

        # sqlalchemy kernel
        'sqlalchemy>=1.2.7',
        'jinja2>=2.8',

        # dev/test - Installed via dev-requirements.txt
        # 'pylint>=1.8.4',
        # 'pytest>=3.5.1',
        # 'recommonmark>=0.4.0',
        # 'rope>=0.10.7',
        # 'Sphinx>=1.7.5',
        # 'sphinx-autobuild>=0.7.1',
        # 'yapf>=0.22.0',
        # 'twine>=1.11.0',
        # 'pre-commit'>=1.10.1',
    ],
    scripts=['bin/dagster']
)
