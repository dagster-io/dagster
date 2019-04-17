import pytest


db = pytest.mark.db
'''Tests that require a database connection.'''

nettest = pytest.mark.nettest
'''Tests that require an internet connection.'''

postgres = pytest.mark.postgres
'''Tests that require a running local Postgres.'''

py3 = pytest.mark.py3
'''Tests that require Python 3.'''

redshift = pytest.mark.redshift
'''Tests that require a running Redshift cluster.'''

skip = pytest.mark.skip

slow = pytest.mark.slow
'''Tests that run slowly (should not run in CI/CD).'''

spark = pytest.mark.spark
'''Tests that require Spark.'''

airflow = pytest.mark.airflow
'''Tests that require Airflow.'''
