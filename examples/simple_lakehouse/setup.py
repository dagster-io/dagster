from setuptools import setup

setup(
    name='simple_lakehouse',
    version='dev',
    author_email='hello@elementl.com',
    packages=['simple_lakehouse'],  # same as name
    install_requires=['dagster'],  # external packages as dependencies
    author='Elementl',
    license='Apache-2.0',
    description='Dagster example for using the Lakehouse API.',
    url='https://github.com/dagster-io/dagster/tree/master/examples/simple_lakehouse',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
)
