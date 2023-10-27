import tempfile

import pytest
from dagster import ConfigurableResource, build_sensor_context, sensor
from dagster._core.instance.ref import InstanceRef


# these tests confirm the existing behavior where user code servers
# do not load the instance to run sensors that do not require resources
# Tracking at https://github.com/dagster-io/dagster/issues/14345
def test_sensor_instance_does_init_with_resource() -> None:
    class MyResource(ConfigurableResource):
        foo: str

    @sensor(job_name="some_job")
    def a_sensor(context, my_resource: MyResource):
        raise Exception("should not execute")

    with tempfile.TemporaryDirectory() as tempdir:
        unloadable_instance_ref = InstanceRef.from_dir(
            tempdir,
            overrides={
                "run_storage": {
                    "module": "dagster._core.test_utils",
                    "class": "ExplodeOnInitRunStorage",
                    "config": {"base_dir": "UNUSED"},
                },
            },
        )
        with pytest.raises(NotImplementedError, match="from_config_value was called"):
            a_sensor(
                build_sensor_context(
                    instance_ref=unloadable_instance_ref,
                    resources={"my_resource": MyResource(foo="bar")},
                )
            )


def test_sensor_instance_does_no_init_with_no_resources() -> None:
    executed = {}

    @sensor(job_name="some_job")
    def a_sensor(context):
        executed["yes"] = True

    with tempfile.TemporaryDirectory() as tempdir:
        unloadable_instance_ref = InstanceRef.from_dir(
            tempdir,
            overrides={
                "run_storage": {
                    "module": "dagster._core.test_utils",
                    "class": "ExplodeOnInitRunStorage",
                    "config": {"base_dir": "UNUSED"},
                },
            },
        )

    with tempfile.TemporaryDirectory() as tempdir:
        unloadable_instance_ref = InstanceRef.from_dir(
            tempdir,
            overrides={
                "run_storage": {
                    "module": "dagster._core.test_utils",
                    "class": "ExplodeOnInitRunStorage",
                    "config": {"base_dir": "UNUSED"},
                },
            },
        )
        a_sensor(build_sensor_context(instance_ref=unloadable_instance_ref))

    assert executed["yes"]
