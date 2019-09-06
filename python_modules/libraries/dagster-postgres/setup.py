import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_postgres/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-postgres':
        return version['__version__']
    elif name == 'dagster-postgres-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-postgres'):
    setup(
        name='dagster_postgres',
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='A Dagster integration for postgres',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-postgres',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        install_requires=[
            'dagster',
            # You can dig into why this is is necessary by digging into some of
            # insanity in this github issue. https://github.com/psycopg/psycopg2/issues/674
            # Essentially we are ensuring here that a version of psycopg is installed
            # that has the binaries installed (they are removed in psycopg 2.8)
            # We would update the dependencies ourselves but this is actually dependent
            # on dependency management of sqlalchemy-redshift or one of its transitive
            # dependencies. They try to install a version of psycopg2 that does
            # not include the binaries and this whole thing breaks.
            # For now we are pinning to a version that we know works. This is probably
            # not flexible enough, but we will resolve that issue when we run into it.
            'psycopg2==2.7.6.1',
            'logx',
        ],
        tests_require=[],
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-postgres-nightly')
    else:
        _do_setup('dagster-postgres')
