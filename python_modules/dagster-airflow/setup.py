import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


def get_version(name):
    version = {}
    with open("dagster_airflow/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122


def _do_setup(name='dagster-airflow'):
    setup(
        name=name,
        version=get_version(name),
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
            # standard python 2/3 compatability things
            'enum34>=1.1.6',
            'future>=0.16.0',
            'dagster>=0.2.0',
        ],
    )


if __name__ == '__main__':
    _do_setup('dagster-airflow')
