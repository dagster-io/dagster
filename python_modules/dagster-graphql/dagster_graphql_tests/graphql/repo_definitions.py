from contextlib import contextmanager

from dagster import (
    DagsterInstance,
    Definitions,
    _check as check,
    asset,
    define_asset_job,
    observable_source_asset,
    schedule,
    sensor,
)
from dagster._config.field_utils import EnvVar
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.test_utils import environ
from dagster_graphql.test.utils import define_out_of_process_context


class MyResource(ConfigurableResource):
    """My description."""

    a_string: str = "baz"
    an_unset_string: str = "defaulted"


@asset
def my_asset(my_resource: MyResource):
    pass


@observable_source_asset
def my_observable_source_asset(my_resource: MyResource):
    pass


@sensor(asset_selection=AssetSelection.all())
def my_sensor(my_resource: MyResource):
    pass


@sensor(asset_selection=AssetSelection.all())
def my_sensor_two(my_resource: MyResource):
    pass


my_asset_job = define_asset_job(name="my_asset_job", selection=AssetSelection.assets(my_asset))


@schedule(job_name="my_asset_job", cron_schedule="* * * * *")
def my_schedule(my_resource: MyResource):
    pass


class MyInnerResource(ConfigurableResource):
    a_str: str


class MyOuterResource(ConfigurableResource):
    inner: MyInnerResource


with environ({"MY_STRING": "bar", "MY_OTHER_STRING": "foo"}):
    defs = Definitions(
        assets=[my_asset, my_observable_source_asset],
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
        jobs=[my_asset_job],
        sensors=[my_sensor, my_sensor_two],
        schedules=[my_schedule],
    )


@contextmanager
def define_definitions_test_out_of_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, "defs", instance) as context:
        yield context
