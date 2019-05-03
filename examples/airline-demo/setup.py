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
        'boto3==1.9.*',
        'dagster',
        'dagstermill',
        'dagster-aws',
        'descartes==1.1.0',
        'geopandas==0.4.0',
        'matplotlib==3.0.2; python_version >= "3.5"',
        'matplotlib==2.2.4; python_version < "3.5"',
        # pyproj is required by geopandas, but something is wrong with the
        # wheel for 2.0.2
        'pyproj==2.0.1',
        'pyspark==2.4.0',
        # You can dig into why this is is necessary by digging into some of
        # insanity in this github issue. https://github.com/psycopg/psycopg2/issues/674
        # Essentially we are ensuring here that a version of psycopg is installed
        # that has the binaries installed (they are removed in psycopg 2.8)
        # We would update the dependencies ourselves but this is actually dependent
        # on dependency management of sqlalchemy-redshift or one of its transitive
        # dependencies. They try to install a version of psycopg2 that does
        # not include the binaries and this whole thing breaks.
        # For now we are pinning to a version that we know works. This is probably
        # not flexible enough, but we will resolve that issue when we run into it.
        'psycopg2==2.7.6.1',
        'sqlalchemy-redshift>=0.7.2',
        'SQLAlchemy-Utils==0.33.8',
    ],
    extras_require={'airflow': ['dagster_airflow', 'docker-compose==1.23.2']},
)
