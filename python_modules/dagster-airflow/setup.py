import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_airflow/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-airflow':
        return version['__version__']
    elif name == 'dagster-airflow-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')

kubernetes = ['kubernetes>=3.0.0', 'cryptography>=2.0.0']


def _do_setup(name='dagster-airflow'):
    ver = get_version(name)
    setup(
        name=name,
        version=ver,
        author='Elementl',
        license='Apache-2.0',
        description='Airflow plugin for Dagster',
        url='https://github.com/dagster-io/dagster',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['dagster_airflow_tests']),
        install_requires=[
            'six',
            'dagster=={ver}'.format(ver=ver),
            'dagster-graphql=={ver}'.format(ver=ver),
            'docker',
            'python-dateutil>=2.8.0',
            # This pin because https://github.com/lepture/flask-wtf/issues/394
            # Our issue: https://github.com/dagster-io/dagster/issues/2119
            'werkzeug<1.0.0',
        ],
        extras_require={'kubernetes': kubernetes},
        entry_points={'console_scripts': ['dagster-airflow = dagster_airflow.cli:main']},
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-airflow-nightly')
    else:
        _do_setup('dagster-airflow')
