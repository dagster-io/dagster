import os
from contextlib import contextmanager

from dagster.utils.test.postgres_instance import postgres_instance_for_test

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def docker_postgres_instance(overrides=None, conn_args=None):
    with postgres_instance_for_test(
        __file__,
        "test-postgres-db-docker",
        overrides=overrides,
        conn_args=conn_args,
    ) as instance:
        yield instance
