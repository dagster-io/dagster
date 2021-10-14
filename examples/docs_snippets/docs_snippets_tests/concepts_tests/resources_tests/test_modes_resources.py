from dagster import build_init_resource_context, build_solid_context, execute_pipeline
from docs_snippets.concepts.modes_resources.modes_resources import (
    cereal_fetcher,
    db_resource,
    emit_foo,
    foo_resource,
    pipeline_with_mode,
    solid_requires_resources,
    test_cm_resource,
    test_my_resource,
    test_my_resource_with_context,
)


def test_cereal_fetcher():
    assert cereal_fetcher(None)


def test_database_resource():
    class BasicDatabase:
        def execute_query(self, query):
            pass

    solid_requires_resources(build_solid_context(resources={"database": BasicDatabase()}))


def test_resource_testing_examples():
    test_my_resource()
    test_my_resource_with_context()
    test_cm_resource()


def test_pipeline_with_mode_example():
    result = execute_pipeline(pipeline_with_mode, mode="ab_mode")
    assert result.success

    result = execute_pipeline(pipeline_with_mode, mode="c_mode")
    assert result.success


def test_resource_dependencies_example():
    assert emit_foo(build_init_resource_context(resources={"foo": foo_resource})) == "foo"


def test_resource_config_example():
    dbconn = db_resource(build_init_resource_context(config={"connection": "foo"}))
    assert dbconn.connection == "foo"
