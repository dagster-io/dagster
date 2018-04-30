import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

setup(
    name='<<name goes here>>',
    author='Nicholas Schrock',
    author_email='schrockn@gmail.com',
    license='MIT',
    packages=find_packages(exclude=['<<test folder>>']),
    install_requires=[
        # standard python 2/3 compatabilitiy things
        'enum34>=1.1.6',
        'future>=0.16.0',
    ],
)
