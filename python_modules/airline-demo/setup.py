import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

version = {}
with open("airline_demo/version.py") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setup(
    name='airline_demo',
    version=version['__version__'],
    author='Elementl',
    license='Apache-2.0',
    description='A complete demo exercising the functionality of Dagster.',
    url='https://github.com/dagster-io/airline-demo',
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
        'dagster',
        'dagstermill',
        'descartes==1.1.0',
        'geopandas==0.4.0',
        'matplotlib==3.0.2; python_version >= "3.5"',
        'matplotlib==2.2.4; python_version < "3.5"',
        # pyproj is required by geopandas, but something is wrong with the
        # wheel for 2.0.2
        'pyproj==2.0.2',
        'pyspark==2.4.0',
        'sqlalchemy-redshift==0.7.1',
        'SQLAlchemy-Utils==0.33.8',
    ],
)
