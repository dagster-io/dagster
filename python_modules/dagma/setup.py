import argparse
import sys
import os

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


def _long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.rst'), 'r') as fh:
        return fh.read()


def get_version(name):
    version = {}
    with open("dagma/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagma':
        return version['__version__']
    else:
        return version['__version__'] + version['__nightly__']


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagma'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='Dagma is an experimental AWS Lambda-based execution engine for dagster pipelines.',
        long_description=_long_description(),
        long_description_content_type='text/markdown',
        url='https://github.com/dagster-io/dagster',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['dagma_tests']),
        install_requires=[
            'boto3==1.9.67',
            'cloudpickle==0.3.1',
            (
                'dagster @ git+https://github.com/dagster-io/dagster.git'
                '@master#egg=dagster&subdirectory=python_modules/dagster'
            ),
            'glob2==0.6',
        ],
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagma-nightly')
    else:
        _do_setup('dagma')
