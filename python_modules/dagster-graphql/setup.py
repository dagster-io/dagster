import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_graphql/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-graphql':
        return version['__version__']
    elif name == 'dagster-graphql-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-graphql'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='The GraphQL frontend to python dagster.',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-graphql',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        install_requires=['graphene>=2.1.3', 'gevent-websocket>=0.10.1', 'gevent', 'requests',],
        entry_points={'console_scripts': ['dagster-graphql = dagster_graphql.cli:main']},
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    print(parsed, unparsed)
    if parsed.nightly:
        _do_setup('dagster-graphql-nightly')
    else:
        _do_setup('dagster-graphql')
