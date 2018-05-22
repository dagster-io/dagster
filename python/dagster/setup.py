import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

setup(
    name='dagster',
    license='MIT',
    packages=find_packages(exclude=['dagster_tests']),
    install_requires=[
        # standard python 2/3 compatability things
        'enum34>=1.1.6',
        'future>=0.16.0',

        # core (not explicitly expressed atm)
        'six>=1.11.0',
        'toposort>=1.5',
        'graphviz>=0.8.3',
        'pyyaml>=3.12',

        # pandas kernel
        'pandas>=0.22.0',
        'pyarrow>=0.8.0',

        # sqlalchemy kernel
        'sqlalchemy>=1.2.7',

        # examples
        'great-expectations>=0.4.1',
        'requests>=2.18.4',
    ],
)
