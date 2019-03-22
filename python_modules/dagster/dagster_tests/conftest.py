import pytest


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-airflow-scratch'
