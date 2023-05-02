from typing import cast

from dagster import (
    ConfigurableResource,
    Definitions,
    FixedConfig,
    Shape,
    job,
    op,
)


def test_fixed_config_hides_field_from_schema() -> None:
    class MyLoginResource(ConfigurableResource):
        username: str
        password: str

    populated = MyLoginResource(username="foo", password=FixedConfig("bar"))
    assert cast(
        Shape, populated.get_resource_definition().config_schema.as_field().config_type
    ).fields.keys() == {"username"}


def test_fixed_config_with_job() -> None:
    executed = {}

    class MyLoginResource(ConfigurableResource):
        username: str
        password: str

    @op
    def my_op(login: MyLoginResource):
        assert login.username == "foo"
        assert login.password == "bar"
        executed["yes"] = True

    @job
    def my_job():
        my_op()

    defs = Definitions(
        jobs=[my_job],
        resources={"login": MyLoginResource(username="foo", password=FixedConfig("bar"))},
    )
    assert defs.get_job_def("my_job").execute_in_process().success
    assert executed["yes"]
