from setuptools import find_packages, setup

setup(
    name='automation',
    version='0.0.1',
    author='Elementl',
    license='Apache-2.0',
    description='Tools for infrastructure automation',
    url='https://github.com/dagster-io/dagster/tree/master/python_modules/automation',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=['test']),
    install_requires=[
        'autoflake',
        'boto3==1.9.*',
        'click>=6.7',
        'pandas',
        'pytablereader',
        'requests',
    ],
)
