import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open("dagster_airflow/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-airflow':
        return version['__version__']
    elif name == 'dagster-airflow-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


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
            # https://github.com/apache/airflow/pull/3723
            # 'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['dagster_airflow_tests']),
        install_requires=[
            # standard python 2/3 compatability things
            'enum-compat==0.0.2',
            'future>=0.16.0, <0.17.0a0',  # pin to range for Airflow compat
            'six>=1.11.0',
            # airflow
            'apache-airflow>=1.10.2; python_version<"3.7"',
            'apache-airflow>=1.10.3; python_version>="3.7"',
            # dagster
            'dagster=={ver}'.format(ver=ver),
            # docker api
            'docker==3.7.0',
            # aws
            'boto3==1.9.*',
            'python-dateutil>=2.8.0',
        ],
        entry_points={"console_scripts": ['dagster-airflow = dagster_airflow.cli:main']},
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-airflow-nightly')
    else:
        _do_setup('dagster-airflow')
