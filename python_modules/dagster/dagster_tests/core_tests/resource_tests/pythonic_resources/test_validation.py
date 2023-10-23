from typing import Optional

import pytest
from dagster import Definitions, asset, job, op
from dagster._config.pythonic_config import Config, ConfigurableResource
from dagster._core.errors import DagsterResourceFunctionError
from pydantic import ValidationError, validator


def test_validator_default_contract_nested() -> None:
    # ensures Pydantic's validator decorator works as expected
    # in particular that it does not validate default values
    # but does validate any explicit inputs matching the default
    class InnerConfig(Config):
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Inner always errors with a non-default value!")

    class MyResource(ConfigurableResource):
        inner: InnerConfig
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Resource always errors with a non-default value!")

    MyResource(inner=InnerConfig())
    with pytest.raises(ValidationError, match="Resource always errors with a non-default value!"):
        MyResource(inner=InnerConfig(), name=None)
    with pytest.raises(ValidationError, match="Inner always errors with a non-default value!"):
        MyResource(inner=InnerConfig(name=None))

    executed = {}

    @op
    def my_op(resource: MyResource) -> None:
        executed["my_op"] = True

    @job
    def my_job() -> None:
        my_op()

    assert my_job.execute_in_process(
        resources={"resource": MyResource(inner=InnerConfig())}
    ).success
    assert executed["my_op"]

    executed.clear()


def test_validator_default_contract_runtime_config() -> None:
    # as above, runtime resource configuration
    class InnerConfig(Config):
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Inner always errors with a non-default value!")

    class MyResource(ConfigurableResource):
        inner: InnerConfig
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Resource always errors with a non-default value!")

    executed = {}

    @asset
    def hello_world_asset(my_resource: MyResource):
        executed["hello_world_asset"] = True

    defs = Definitions(
        assets=[hello_world_asset],
        resources={"my_resource": MyResource.configure_at_launch()},
    )

    defs.get_implicit_global_asset_job_def().execute_in_process()
    assert executed["hello_world_asset"]

    with pytest.raises(DagsterResourceFunctionError):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            {"resources": {"my_resource": {"config": {"name": None}}}}
        )
