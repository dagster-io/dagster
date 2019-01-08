import argparse
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

parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-sqlalchemy'):
    setup(
        name=name,
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
        packages=find_packages(exclude=['dagster_sqlalchemy_tests']),
        install_requires=['dagster', 'dagstermill', 'jinja2>=2.8', 'sqlalchemy>=1.2.7'],
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-sqlalchemy-nightly')
    else:
        _do_setup('dagster-sqlalchemy')
