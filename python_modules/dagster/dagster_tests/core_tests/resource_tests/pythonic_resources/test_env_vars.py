import os
from typing import List, Mapping

import pytest
from dagster import (
    Config,
    ConfigurableResource,
    Definitions,
    EnvVar,
    asset,
)
from dagster._core.errors import (
    DagsterInvalidConfigError,
)
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
            .execute_in_process(
                {"resources": {"writer": {"config": {"prefix": EnvVar("MY_PREFIX_FOR_TEST")}}}}
            )
            .success
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
