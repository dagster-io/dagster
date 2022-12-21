from dagster import build_init_resource_context, build_op_context
from docs_snippets.concepts.resources.resources import (
    cereal_fetcher,
    connect,
    db_connection,
    db_resource,
    do_database_stuff_dev,
    do_database_stuff_job,
    do_database_stuff_prod,
    op_requires_resources,
    test_cm_resource,
    test_my_resource,
    test_my_resource_with_context,
    use_db_connection,
    uses_db_connection,
)


def test_cereal_fetcher():
    assert cereal_fetcher(None)


def test_database_resource():
    class BasicDatabase:
        def execute_query(self, query):
            pass

    op_requires_resources(build_op_context(resources={"database": BasicDatabase()}))


def test_resource_testing_examples():
    test_my_resource()
    test_my_resource_with_context()
    test_cm_resource()


def test_resource_deps_job():
    result = connect.execute_in_process()
    assert result.success


def test_resource_config_example():
    dbconn = db_resource(build_init_resource_context(config={"connection": "foo"}))
    assert dbconn.connection == "foo"


def test_jobs():
    assert do_database_stuff_job.execute_in_process().success
    assert do_database_stuff_dev.execute_in_process().success
    assert do_database_stuff_prod.execute_in_process().success


def test_cm_resource_example():
    with db_connection() as db_conn:
        assert db_conn


def test_cm_resource_op():
    with build_op_context(resources={"db_connection": db_connection}) as context:
        use_db_connection(context)


def test_build_resources_example():
    uses_db_connection()
