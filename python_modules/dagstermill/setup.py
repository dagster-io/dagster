import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

version = {}
with open("dagstermill/version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setup(
    name='dagstermill',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    packages=find_packages(exclude=['dagstermill_tests']),
    install_requires=[
        # standard python 2/3 compatability things
        'enum34>=1.1.6',
        'future>=0.16.0',
        'papermill>=0.15.0',
        'ipykernel>=4.9.0',
    ],
)
