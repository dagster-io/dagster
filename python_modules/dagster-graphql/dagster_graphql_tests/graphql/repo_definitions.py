from contextlib import contextmanager

from dagster import (
    ConfigVerifiable,
    DagsterInstance,
    Definitions,
    VerificationResult,
    VerificationStatus,
    _check as check,
    asset,
)
from dagster._config.field_utils import EnvVar
from dagster._config.structured_config import ConfigurableResource
from dagster._core.test_utils import environ
from dagster_graphql.test.utils import define_out_of_process_context


@asset
def my_asset():
    pass


count = 0


class MyResource(ConfigurableResource, ConfigVerifiable):
    """My description."""

    a_string: str = "baz"
    an_unset_string: str = "defaulted"

    def verify_config(self) -> VerificationResult:
        global count  # noqa: PLW0603
        count += 1
        if count % 2 == 0:
            return VerificationResult(VerificationStatus.FAILURE, "even")
        else:
            return VerificationResult(VerificationStatus.SUCCESS, "odd")


class MyInnerResource(ConfigurableResource):
    a_str: str


class MyOuterResource(ConfigurableResource):
    inner: MyInnerResource


with environ({"MY_STRING": "bar", "MY_OTHER_STRING": "foo"}):
    defs = Definitions(
        assets=[my_asset],
        resources={
            "foo": "a_string",
            "my_resource": MyResource(
                a_string="foo",
            ),
            "my_resource_env_vars": MyResource(a_string=EnvVar("MY_STRING")),
            "my_resource_two_env_vars": MyResource(
                a_string=EnvVar("MY_STRING"), an_unset_string=EnvVar("MY_OTHER_STRING")
            ),
            "my_outer_resource": MyOuterResource(
                inner=MyInnerResource(a_str="wrapped"),
            ),
        },
    )


@contextmanager
def define_definitions_test_out_of_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, "defs", instance) as context:
        yield context
