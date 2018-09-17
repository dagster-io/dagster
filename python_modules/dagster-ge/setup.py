import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

setup(
    name='dagster-ge',
    version='0.2.0',
    author='Elementl',
    license='Apache-2.0',
    description='Great Expectations plugin for Dagster',
    url='https://github.com/dagster-io/dagster',
    classifiers=(
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ),
    packages=find_packages(exclude=['dagster_tests']),
    install_requires=[
        # standard python 2/3 compatability things
        'enum34>=1.1.6',
        'future>=0.16.0',
        'dagster>=0.2.0',
        'great-expectations>=0.4.2',
    ]
    # scripts=['bin/dagster']
)
