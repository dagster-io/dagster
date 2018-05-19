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

        # solidic (not explicitly expressed atm)
        'graphviz>=0.8.3',
        'pyyaml-3.12',
    ],
)
