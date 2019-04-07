import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

version = {}
with open("dagster_graphql/version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setup(
    name='dagster_graphql',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description='The GraphQL frontend to python dagster.',
    url='https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-graphql',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=['test']),
    install_requires=[
        'graphene>=2.1.3',
        'gevent-websocket==0.10.1',
        'gevent==1.3.7',
        'pyrsistent>=0.14.8',
        'rx>=1.6.1',
    ],
)
