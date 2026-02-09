import enum
import os
from collections.abc import Mapping

import dagster as dg
import pytest
from dagster._core.test_utils import environ


def test_env_var() -> None:
    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):

        class ResourceWithString(dg.ConfigurableResource):
            a_str: str

        executed = {}

        @dg.asset
        def an_asset(a_resource: ResourceWithString):
            assert a_resource.a_str == "SOME_VALUE"
            executed["yes"] = True

        defs = dg.Definitions(
            assets=[an_asset],
            resources={
                "a_resource": ResourceWithString(
                    a_str=dg.EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            },
        )

        assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_data_structure() -> None:
    with environ(
        {
            "FOO": "hello",
            "BAR": "world",
        }
    ):

        class ResourceWithString(dg.ConfigurableResource):
            my_list: list[str]
            my_dict: Mapping[str, str]

        executed = {}

        @dg.asset
        def an_asset(a_resource: ResourceWithString):
            assert len(a_resource.my_list) == 2
            assert a_resource.my_list[0] == "hello"
            assert a_resource.my_list[1] == "world"
            assert len(a_resource.my_dict) == 2
            assert a_resource.my_dict["foo"] == "hello"
            assert a_resource.my_dict["bar"] == "world"
            executed["yes"] = True

        defs = dg.Definitions(
            assets=[an_asset],
            resources={
                "a_resource": ResourceWithString(
                    my_list=[dg.EnvVar("FOO"), dg.EnvVar("BAR")],  # type: ignore[arg-type]
                    my_dict={
                        "foo": dg.EnvVar("FOO"),
                        "bar": dg.EnvVar("BAR"),
                    },
                )
            },
        )

        assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_runtime_config_env_var() -> None:
    out_txt = []

    class WriterResource(dg.ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @dg.asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    defs = dg.Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.configure_at_launch()},
    )

    with environ({"MY_PREFIX_FOR_TEST": "greeting: "}):
        with pytest.raises(dg.DagsterInvalidConfigError):
            defs.resolve_implicit_global_asset_job_def().execute_in_process(
                {"resources": {"writer": {"config": {"prefix": dg.EnvVar("MY_PREFIX_FOR_TEST")}}}}
            )

        # Ensure fully unstructured run config option works
        result = defs.resolve_implicit_global_asset_job_def().execute_in_process(
            {"resources": {"writer": {"config": {"prefix": {"env": "MY_PREFIX_FOR_TEST"}}}}}
        )
        assert result.success
        assert out_txt[0] == "greeting: hello, world!"


def test_env_var_err() -> None:
    if "UNSET_ENV_VAR" in os.environ:
        del os.environ["UNSET_ENV_VAR"]

    class ResourceWithString(dg.ConfigurableResource):
        a_str: str

    @dg.asset
    def an_asset(a_resource: ResourceWithString):
        pass

    # No error constructing the resource, only at runtime
    defs = dg.Definitions(
        assets=[an_asset],
        resources={
            "a_resource": ResourceWithString(
                a_str=dg.EnvVar("UNSET_ENV_VAR"),
            )
        },
    )
    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match=(
            r'You have attempted to fetch the environment variable "UNSET_ENV_VAR" which is not set.'
        ),
    ):
        defs.resolve_implicit_global_asset_job_def().execute_in_process()

    # Test using runtime configuration of the resource
    defs = dg.Definitions(
        assets=[an_asset],
        resources={"a_resource": ResourceWithString.configure_at_launch()},
    )
    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match=r"Invalid use of environment variable wrapper.",
    ):
        defs.resolve_implicit_global_asset_job_def().execute_in_process(
            {"resources": {"a_resource": {"config": {"a_str": dg.EnvVar("UNSET_ENV_VAR_RUNTIME")}}}}
        )


def test_env_var_nested_resources() -> None:
    class ResourceWithString(dg.ConfigurableResource):
        a_str: str

    class OuterResource(dg.ConfigurableResource):
        inner: ResourceWithString

    executed = {}

    @dg.asset
    def an_asset(a_resource: OuterResource):
        assert a_resource.inner.a_str == "SOME_VALUE"
        executed["yes"] = True

    defs = dg.Definitions(
        assets=[an_asset],
        resources={
            "a_resource": OuterResource(
                inner=ResourceWithString(
                    a_str=dg.EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            )
        },
    )

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_nested_config() -> None:
    class NestedWithString(dg.Config):
        a_str: str

    class OuterResource(dg.ConfigurableResource):
        inner: NestedWithString

    executed = {}

    @dg.asset
    def an_asset(a_resource: OuterResource):
        assert a_resource.inner.a_str == "SOME_VALUE"
        executed["yes"] = True

    defs = dg.Definitions(
        assets=[an_asset],
        resources={
            "a_resource": OuterResource(
                inner=NestedWithString(
                    a_str=dg.EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            )
        },
    )

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_alongside_enum() -> None:
    class MyEnum(enum.Enum):
        FOO = "foofoo"
        BAR = "barbar"

    class ResourceWithStringAndEnum(dg.ConfigurableResource):
        a_str: str
        my_enum: MyEnum

    executed = {}

    @dg.asset
    def an_asset(a_resource: ResourceWithStringAndEnum):
        executed["yes"] = True
        return a_resource.my_enum.name, a_resource.a_str

    defs = dg.Definitions(
        assets=[an_asset],
        resources={
            "a_resource": ResourceWithStringAndEnum(
                a_str=dg.EnvVar("ENV_VARIABLE_FOR_TEST"),
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
        result = defs.resolve_implicit_global_asset_job_def().execute_in_process()
        assert result.output_for_node("an_asset") == ("FOO", "SOME_VALUE")
        assert executed["yes"]

    executed.clear()

    # Case: I'm using the default value provided by resource instantiation to the enum, and then using a value specified at runtime for the string.
    result = defs.resolve_implicit_global_asset_job_def().execute_in_process(
        run_config={"resources": {"a_resource": {"config": {"a_str": "foo", "my_enum": "BAR"}}}}
    )

    assert result.success
    assert result.output_for_node("an_asset") == ("BAR", "foo")
    assert executed["yes"]


def test_env_var_err_at_instantiation() -> None:
    if "UNSET_ENV_VAR" in os.environ:
        del os.environ["UNSET_ENV_VAR"]

    class ResourceWithString(dg.ConfigurableResource):
        a_str: str

    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match=(
            r'You have attempted to fetch the environment variable "UNSET_ENV_VAR" which is not set.'
        ),
    ):
        ResourceWithString(
            a_str=dg.EnvVar("UNSET_ENV_VAR"),
        ).process_config_and_initialize()
