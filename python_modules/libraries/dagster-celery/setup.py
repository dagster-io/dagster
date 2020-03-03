import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_celery/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-celery':
        return version['__version__']
    elif name == 'dagster-celery-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-celery'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='Package for using Celery as Dagster\'s execution engine.',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-celery',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        entry_points={'console_scripts': ['dagster-celery = dagster_celery.cli:main']},
        install_requires=['dagster', 'dagster_graphql', 'celery>=4.3.0', 'click>=5.0',],
        extras_require={'flower': ['flower'], 'redis': ['redis']},
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed

    if parsed.nightly:
        _do_setup('dagster-celery-nightly')
    else:
        _do_setup('dagster-celery')
