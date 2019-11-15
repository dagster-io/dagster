from setuptools import find_packages, setup

setup(
    name='dagster_examples',
    version='dev',
    author='Elementl',
    license='Apache-2.0',
    description='Dagster Examples',
    url='https://github.com/dagster-io/dagster',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=['test']),
    # default supports basic tutorial & toy examples
    install_requires=['dagster'],
    extras_require={
        # full is for running the more realistic demos
        'full': [
            'dagstermill',
            'dagster-aws',
            'dagster-cron',
            'dagster-postgres',
            'dagster-slack',
            'dagster-snowflake',
            'descartes==1.1.0',
            'geopandas==0.4.0',
            'google-api-python-client',
            'google-cloud-storage',
            'matplotlib==3.0.2; python_version >= "3.5"',
            'matplotlib==2.2.4; python_version < "3.5"',
            'mock==2.0.0',
            'pytest-mock',
            # pyproj is required by geopandas, but something is wrong with the
            # wheel for 2.0.2
            'pyproj==2.0.1',
            'pyspark==2.4.4',
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
        'dbt': [
            'dbt-postgres',
            # pin werkzeug pending https://github.com/fishtown-analytics/dbt/issues/1697
            # for Flask compatibility
            'werkzeug>=0.15.0',
        ],
        'airflow': ['dagster_airflow', 'docker-compose==1.23.2'],
    },
    include_package_data=True,
)
