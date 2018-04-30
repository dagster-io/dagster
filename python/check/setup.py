import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

setup(
    name='check',
    license='MIT',
    packages=find_packages(exclude=['check_tests']),
    install_requires=[
        'future>=0.16.0',

        # tests
        'pytest>=3.5.1',
    ],
)
