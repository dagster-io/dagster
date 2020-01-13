import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_github/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-github':
        return version['__version__']
    elif name == 'dagster-github-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-github'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='A Github client resource for interacting with the github API with a github App',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-github',
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
            # Using a Github app requires signing your own JWT :(
            # https://developer.github.com/apps/building-github-apps/authenticating-with-github-apps/
            'pyjwt[crypto]',
            # No officially supported python sdk for github :(
            'requests',
        ],
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-github-nightly')
    else:
        _do_setup('dagster-github')
