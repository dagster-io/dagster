import os

import pytest

# pylint: disable=unused-import
from .cluster import dagster_instance, define_cluster_provider_fixture, run_launcher
from .helm import helm_namespace


@pytest.fixture(scope='session', autouse=True)
def dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    os.environ['DAGSTER_HOME'] = '/opt/dagster/dagster_home'
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env


cluster_provider = define_cluster_provider_fixture(
    additional_kind_images=['docker.io/bitnami/rabbitmq', 'docker.io/bitnami/postgresql']
)
