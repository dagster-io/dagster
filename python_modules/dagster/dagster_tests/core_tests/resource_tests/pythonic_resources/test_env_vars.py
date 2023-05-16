import enum
import os
from enum import Enum
from typing import List, Mapping

import pytest
from dagster import (
    Config,
    ConfigurableResource,
    Definitions,
    EnvVar,
    asset,
    materialize,
)
from dagster._core.errors import (
    DagsterInvalidConfigError,
)
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.test_utils import environ


def test_enum_nested_resource() -> None:
    class MyEnum(Enum):
        A = "a_value"
        B = "b_value"

    class ResourceWithEnum(ConfigurableResource):
        my_enum: MyEnum

    class OuterResourceWithResourceWithEnum(ConfigurableResource):
        resource_with_enum: ResourceWithEnum

    @asset
    def asset_with_outer_resource(outer_resource: OuterResourceWithResourceWithEnum):
        return outer_resource.resource_with_enum.my_enum.value

    defs = Definitions(
        assets=[asset_with_outer_resource],
        resources={
            "outer_resource": OuterResourceWithResourceWithEnum(
                resource_with_enum=ResourceWithEnum(my_enum=MyEnum.A)
            )
        },
    )

    a_job = defs.get_implicit_global_asset_job_def()

    result = a_job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_with_outer_resource") == "a_value"


def test_basic_enum_override_with_resource_configured_at_launch() -> None:
    class MyEnum(Enum):
        A = "a_value"
        B = "b_value"

    class MyResource(ConfigurableResource):
        my_enum: MyEnum

    @asset
    def asset_with_resource(context, my_resource: MyResource):
        return my_resource.my_enum.value

    result_one = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource.configure_at_launch()},
        run_config={"resources": {"my_resource": {"config": {"my_enum": "B"}}}},
    )

    assert result_one.success
    assert result_one.output_for_node("asset_with_resource") == "b_value"

    result_two = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource.configure_at_launch(my_enum=MyEnum.A)},
        run_config={"resources": {"my_resource": {"config": {"my_enum": "B"}}}},
    )

    assert result_two.success
    assert result_two.output_for_node("asset_with_resource") == "b_value"


def test_env_var_alongside_enum() -> None:
    class MyEnum(enum.Enum):
        FOO = "foofoo"
        BAR = "barbar"

    class ResourceWithStringAndEnum(ConfigurableResource):
        a_str: str
        my_enum: MyEnum

    executed = {}

    @asset
    def an_asset(a_resource: ResourceWithStringAndEnum):
        executed["yes"] = True
        return a_resource.my_enum.name, a_resource.a_str

    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": ResourceWithStringAndEnum(
                a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                my_enum=MyEnum.FOO,
            )
        },
    )

    # Case: I'm using the default value provided by resource instantiation for the enum, and then using the env var specified at instantiation time for the string.
    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        result = defs.get_implicit_global_asset_job_def().execute_in_process()
        assert result.output_for_node("an_asset") == ("FOO", "SOME_VALUE")
        assert executed["yes"]

    executed.clear()

    # Case: I'm re-specifying the same env var value at runtime for the env var
    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        result = defs.get_implicit_global_asset_job_def().execute_in_process(
            run_config={
                "resources": {
                    "a_resource": {
                        "config": {"a_str": EnvVar("ENV_VARIABLE_FOR_TEST"), "my_enum": "BAR"}
                    }
                }
            }
        )

        assert result.success
        assert result.output_for_node("an_asset") == ("BAR", "SOME_VALUE")
        assert executed["yes"]

    # Case: I'm using a new value specified at runtime for the enum, and then using a new env var specified at instantiation time for the string.
    with environ(
        {
            "OTHER_ENV_VARIABLE_FOR_TEST": "OTHER_VALUE",
        }
    ):
        result = defs.get_implicit_global_asset_job_def().execute_in_process(
            run_config={
                "resources": {
                    "a_resource": {
                        "config": {"a_str": EnvVar("OTHER_ENV_VARIABLE_FOR_TEST"), "my_enum": "BAR"}
                    }
                }
            }
        )

        assert result.success
        assert result.output_for_node("an_asset") == ("BAR", "OTHER_VALUE")
        assert executed["yes"]

    # Case: I'm using the default value provided by resource instantiation to the enum, and then using a value specified at runtime for the string.
    result = defs.get_implicit_global_asset_job_def().execute_in_process(
        run_config={"resources": {"a_resource": {"config": {"a_str": "foo", "my_enum": "BAR"}}}}
    )

    assert result.success
    assert result.output_for_node("an_asset") == ("BAR", "foo")
    assert executed["yes"]


def test_env_var() -> None:
    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):

        class ResourceWithString(ConfigurableResource):
            a_str: str

        executed = {}

        @asset
        def an_asset(a_resource: ResourceWithString):
            assert a_resource.a_str == "SOME_VALUE"
            executed["yes"] = True

        defs = Definitions(
            assets=[an_asset],
            resources={
                "a_resource": ResourceWithString(
                    a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            },
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_data_structure() -> None:
    with environ(
        {
            "FOO": "hello",
            "BAR": "world",
        }
    ):

        class ResourceWithString(ConfigurableResource):
            my_list: List[str]
            my_dict: Mapping[str, str]

        executed = {}

        @asset
        def an_asset(a_resource: ResourceWithString):
            assert len(a_resource.my_list) == 2
            assert a_resource.my_list[0] == "hello"
            assert a_resource.my_list[1] == "world"
            assert len(a_resource.my_dict) == 2
            assert a_resource.my_dict["foo"] == "hello"
            assert a_resource.my_dict["bar"] == "world"
            executed["yes"] = True

        defs = Definitions(
            assets=[an_asset],
            resources={
                "a_resource": ResourceWithString(
                    my_list=[EnvVar("FOO"), EnvVar("BAR")],
                    my_dict={
                        "foo": EnvVar("FOO"),
                        "bar": EnvVar("BAR"),
                    },
                )
            },
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_runtime_config_env_var() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.configure_at_launch()},
    )

    os.environ["MY_PREFIX_FOR_TEST"] = "greeting: "
    try:
        assert (
            defs.get_implicit_global_asset_job_def()
            # I do not think this should work. Worth discussing in PR.
            # .execute_in_process(
            #     {"resources": {"writer": {"config": {"prefix": EnvVar("MY_PREFIX_FOR_TEST")}}}}
            # )
            .execute_in_process(
                {"resources": {"writer": {"config": {"prefix": {"env": "MY_PREFIX_FOR_TEST"}}}}}
            ).success
        )
        assert out_txt == ["greeting: hello, world!"]
    finally:
        del os.environ["MY_PREFIX_FOR_TEST"]


def test_env_var_err() -> None:
    if "UNSET_ENV_VAR" in os.environ:
        del os.environ["UNSET_ENV_VAR"]

    class ResourceWithString(ConfigurableResource):
        a_str: str

    @asset
    def an_asset(a_resource: ResourceWithString):
        pass

    # No error constructing the resource, only at runtime
    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": ResourceWithString(
                a_str=EnvVar("UNSET_ENV_VAR"),
            )
        },
    )
    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            'You have attempted to fetch the environment variable "UNSET_ENV_VAR" which is not set.'
        ),
    ):
        defs.get_implicit_global_asset_job_def().execute_in_process()

    # Test using runtime configuration of the resource
    defs = Definitions(
        assets=[an_asset],
        resources={"a_resource": ResourceWithString.configure_at_launch()},
    )
    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            'You have attempted to fetch the environment variable "UNSET_ENV_VAR_RUNTIME" which is'
            " not set."
        ),
    ):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            {"resources": {"a_resource": {"config": {"a_str": EnvVar("UNSET_ENV_VAR_RUNTIME")}}}}
        )


def test_env_var_nested_resources() -> None:
    class ResourceWithString(ConfigurableResource):
        a_str: str

    class OuterResource(ConfigurableResource):
        inner: ResourceWithString

    executed = {}

    @asset
    def an_asset(a_resource: OuterResource):
        assert a_resource.inner.a_str == "SOME_VALUE"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": OuterResource(
                inner=ResourceWithString(
                    a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            )
        },
    )

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_nested_config() -> None:
    class NestedWithString(Config):
        a_str: str

    class OuterResource(ConfigurableResource):
        inner: NestedWithString

    executed = {}

    @asset
    def an_asset(a_resource: OuterResource):
        assert a_resource.inner.a_str == "SOME_VALUE"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": OuterResource(
                inner=NestedWithString(
                    a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            )
        },
    )

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_basic_enum_override_with_resource_instance() -> None:
    class MyEnum(Enum):
        A = "a_value"
        B = "b_value"

    setup_executed = {}

    class MyResource(ConfigurableResource):
        my_enum: MyEnum

        def setup_for_execution(self, context: InitResourceContext) -> None:
            setup_executed["yes"] = True
            # confirm existing behavior of config system
            assert context.resource_config["my_enum"] in ["a_value", "b_value"]

    @asset
    def asset_with_resource(context, my_resource: MyResource):
        return my_resource.my_enum.value

    result_one = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource(my_enum=MyEnum.A)},
    )
    assert result_one.success
    assert result_one.output_for_node("asset_with_resource") == "a_value"
    assert setup_executed["yes"]

    setup_executed.clear()

    result_two = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource(my_enum=MyEnum.A)},
        run_config={"resources": {"my_resource": {"config": {"my_enum": "B"}}}},
    )

    assert result_two.success
    assert result_two.output_for_node("asset_with_resource") == "b_value"
    assert setup_executed["yes"]
