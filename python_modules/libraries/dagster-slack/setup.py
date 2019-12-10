import argparse
import sys

from setuptools import find_packages, setup


def get_version(name):
    version = {}
    with open('dagster_slack/version.py') as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-slack':
        return version['__version__']
    elif name == 'dagster-slack-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-slack'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='A Slack client resource for posting to Slack',
        url='https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-slack',
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
            # Slack 2.x does not support Python 2
            # https://github.com/slackapi/python-slackclient/wiki/Migrating-to-2.x#minimum-python-versions
            'slackclient<2.0.0',
        ],
        zip_safe=False,
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-slack-nightly')
    else:
        _do_setup('dagster-slack')
