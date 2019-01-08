import os
import sys

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
with open("dagster_sqlalchemy/version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setup(
    name='dagster_sqlalchemy',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description=(
        'Utilities and examples for working with SQLAlchemy and dagster, an opinionated '
        'framework for expressing data pipelines'
    ),
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/dagster-io/dagster',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    install_requires=['dagster', 'dagstermill', 'jinja2>=2.8', 'sqlalchemy>=1.2.7'],
)
