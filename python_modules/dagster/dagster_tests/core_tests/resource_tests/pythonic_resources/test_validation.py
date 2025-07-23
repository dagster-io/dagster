from typing import Optional

import dagster as dg
import pytest
from pydantic import ValidationError, validator


def test_validator_default_contract_nested() -> None:
    # ensures Pydantic's validator decorator works as expected
    # in particular that it does not validate default values
    # but does validate any explicit inputs matching the default
    class InnerConfig(dg.Config):
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Inner always errors with a non-default value!")

    class MyResource(dg.ConfigurableResource):
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

    @dg.op
    def my_op(resource: MyResource) -> None:
        executed["my_op"] = True

    @dg.job
    def my_job() -> None:
        my_op()

    assert my_job.execute_in_process(
        resources={"resource": MyResource(inner=InnerConfig())}
    ).success
    assert executed["my_op"]

    executed.clear()
