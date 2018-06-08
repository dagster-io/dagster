import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

setup(
    name='dagster',
    license='Apache-2.0',
    packages=find_packages(exclude=['dagster_tests']),
    install_requires=[
        # standard python 2/3 compatability things
        'enum34>=1.1.6',
        'future>=0.16.0',

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
        'jinja2>=2.10',

        # examples
        # unused and very, very heavy
        # 'great-expectations>=0.4.1',
        # 'requests>=2.18.4',

        # dev/test
        'pytest>=3.5.1',
        'pylint>=1.8.4',
        'yapf>=0.21.0',
        'rope>=0.10.7',
    ],
    scripts=['bin/dagster']
)
