from contextlib import contextmanager

from dagster import (
    DagsterInstance,
    Definitions,
    _check as check,
    asset,
)
from dagster._config.structured_config import Resource
from dagster._core.definitions.repository_definition import SINGLETON_REPOSITORY_NAME
from dagster_graphql.test.utils import define_out_of_process_context


@asset
def my_asset():
    pass


class MyResource(Resource):
    """my description"""

    a_string: str = "baz"
    a_bool: bool
    an_unset_string: str = "defaulted"


__repository__ = Definitions(
    assets=[my_asset],
    resources={
        "foo": "a_string",
        "my_resource": MyResource(
            a_string="foo",
            a_bool=True,
        ),
    },
)


@contextmanager
def define_definitions_test_out_of_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, SINGLETON_REPOSITORY_NAME, instance) as context:
        yield context
