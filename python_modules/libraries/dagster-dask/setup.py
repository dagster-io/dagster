import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_dask/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-dask':
        return version['__version__']
    elif name == 'dagster-dask-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-dask'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='Package for using Dask as Dagster\'s execution engine.',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dask',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        install_requires=[
            'bokeh',
            'dagster',
            'dagster_graphql',
            'dask>=1.2.2',
            'distributed>=1.28.1',
        ],
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed

    if sys.version_info[0] < 3 and sys.platform == 'darwin':
        raise Exception('dagster-dask does not work on Python 2 + macOS')

    if parsed.nightly:
        _do_setup('dagster-dask-nightly')
    else:
        _do_setup('dagster-dask')
