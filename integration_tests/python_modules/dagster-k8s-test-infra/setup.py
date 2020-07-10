import argparse
import sys

from setuptools import find_packages, setup

parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-k8s-test-infra'):
    setup(
        name=name,
        author='Elementl',
        author_email='hello@elementl.com',
        license='Apache-2.0',
        description='A Dagster integration for k8s-test-infra',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-k8s-test-infra',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        install_requires=['dagster'],
        tests_require=[],
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    _do_setup('dagster-k8s-test-infra')
