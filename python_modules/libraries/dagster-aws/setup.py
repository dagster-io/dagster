import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_aws/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-aws':
        return version['__version__']
    elif name == 'dagster-aws-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-aws'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='Package for AWS-specific Dagster framework solid and resource components.',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['test']),
        include_package_data=True,
        install_requires=['boto3==1.9.*', 'dagster', 'requests', 'terminaltables'],
        extras_require={'pyspark': ['dagster-pyspark']},
        entry_points={'console_scripts': ['dagster-aws = dagster_aws.cli.cli:main']},
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-aws-nightly')
    else:
        _do_setup('dagster-aws')
