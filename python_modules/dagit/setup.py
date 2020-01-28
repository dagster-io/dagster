import argparse
import os
import sys

from setuptools import find_packages, setup


def long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.rst'), 'r') as fh:
        return fh.read()


def get_version(name):
    version = {}
    with open('dagit/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagit':
        return version['__version__']
    elif name == 'dagit-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagit'):
    ver = get_version(name)
    setup(
        name=name,
        version=ver,
        author='Elementl',
        license='Apache-2.0',
        description='Web UI for dagster.',
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
        packages=find_packages(exclude=['dagit_tests']),
        include_package_data=True,
        install_requires=[
            # standard python 2/3 compatability things
            'enum34; python_version < "3.4"',
            'future',
            'PyYAML',
            # cli
            'click>=7.0',
            'dagster=={ver}'.format(ver=ver),
            'dagster-graphql=={ver}'.format(ver=ver),
            # graphql
            'graphql-core>=2.1,<3',
            # server
            'flask-cors>=3.0.6',
            'Flask-GraphQL>=2.0.0',
            'Flask-Sockets>=0.2.1',
            'flask>=0.12.4',
            'gevent-websocket>=0.10.1',
            'gevent',
            'graphql-ws>=0.3.0',
            # watchdog
            'watchdog>=0.8.3',
            # notebooks support
            'nbconvert>=5.4.0',
        ],
        entry_points={
            'console_scripts': ['dagit-cli = dagit.cli:main', 'dagit = dagit.dagit:main']
        },
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagit-nightly')
    else:
        _do_setup('dagit')
