import enum
import os
from typing import List, Mapping

import pytest
from dagster import Config, ConfigurableResource, Definitions, EnvVar, asset
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.test_utils import environ


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
            my_list: list[str]
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
                    my_list=[EnvVar("FOO"), EnvVar("BAR")],  # type: ignore[arg-type]
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

    with environ({"MY_PREFIX_FOR_TEST": "greeting: "}):
        with pytest.raises(DagsterInvalidConfigError):
            defs.get_implicit_global_asset_job_def().execute_in_process(
                {"resources": {"writer": {"config": {"prefix": EnvVar("MY_PREFIX_FOR_TEST")}}}}
            )

        # Ensure fully unstructured run config option works
        result = defs.get_implicit_global_asset_job_def().execute_in_process(
            {"resources": {"writer": {"config": {"prefix": {"env": "MY_PREFIX_FOR_TEST"}}}}}
        )
        assert result.success
        assert out_txt[0] == "greeting: hello, world!"


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
        match="Invalid use of environment variable wrapper.",
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

    # Case: I'm using the default value provided by resource instantiation to the enum, and then using a value specified at runtime for the string.
    result = defs.get_implicit_global_asset_job_def().execute_in_process(
        run_config={"resources": {"a_resource": {"config": {"a_str": "foo", "my_enum": "BAR"}}}}
    )

    assert result.success
    assert result.output_for_node("an_asset") == ("BAR", "foo")
    assert executed["yes"]
