import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


setup(
    name='automation',
    version='0.0.1',
    author='Elementl',
    license='Apache-2.0',
    description='Tools for infrastructure automation',
    url='https://github.com/dagster-io/dagster',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=['test']),
    install_requires=[
        'boto3==1.9.47',
        'click>=6.7',
        'faker>=1.0.4',
        'pytablereader',
        'random_useragent>=1.0',
        'requests',
    ],
    entry_points={"console_scripts": ['generate_synthetic_events = generate_synthetic_events:run']},
)
