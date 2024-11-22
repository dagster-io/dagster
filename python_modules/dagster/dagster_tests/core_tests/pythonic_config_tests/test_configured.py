from typing import Any, Dict

import pytest
from dagster import Config, RunConfig, configured, job, op
from dagster._check import CheckError


def test_config_mapping_return_config_dict() -> None:
    class DoSomethingConfig(Config):
        config_param: str

    @op
    def do_something(config: DoSomethingConfig) -> str:
        return config.config_param

    class DoSomethingSimplifiedConfig(Config):
        simplified_param: str

    # New, fancy config mapping takes in a Pythonic config object but returns normal config dict
    @configured(do_something)
    def do_something_simplified(config_in: DoSomethingSimplifiedConfig) -> dict[str, Any]:
        return {"config_param": config_in.simplified_param}

    @job
    def do_it_all_with_simplified_config() -> None:
        do_something_simplified()

    result = do_it_all_with_simplified_config.execute_in_process(
        run_config=RunConfig(
            ops={"do_something_simplified": DoSomethingSimplifiedConfig(simplified_param="foo")}
        )
    )
    assert result.success
    assert result.output_for_node("do_something_simplified") == "foo"


def test_config_mapping_return_config_object() -> None:
    class DoSomethingConfig(Config):
        config_param: str

    @op
    def do_something(config: DoSomethingConfig) -> str:
        return config.config_param

    class DoSomethingSimplifiedConfig(Config):
        simplified_param: str

    # New, fancy config mapping takes in a Pythonic config object and returns a config class
    @configured(do_something)
    def do_something_simplified(config_in: DoSomethingSimplifiedConfig) -> DoSomethingConfig:
        return DoSomethingConfig(config_param=config_in.simplified_param)

    @job
    def do_it_all_with_simplified_config() -> None:
        do_something_simplified()

    result = do_it_all_with_simplified_config.execute_in_process(
        run_config=RunConfig(
            ops={"do_something_simplified": DoSomethingSimplifiedConfig(simplified_param="foo")}
        )
    )
    assert result.success
    assert result.output_for_node("do_something_simplified") == "foo"


def test_config_annotation_no_config_schema_err() -> None:
    class DoSomethingConfig(Config):
        config_param: str

    @op
    def do_something(config: DoSomethingConfig) -> str:
        return config.config_param

    class DoSomethingSimplifiedConfig(Config):
        simplified_param: str

    # Ensure that we error if we try to provide a config_schema to a @configured function
    # which has a Config-annotated param - no need to provide a config_schema in this case
    with pytest.raises(
        CheckError,
        match="Cannot provide config_schema to @configured function with Config-annotated param",
    ):

        @configured(do_something, config_schema={"simplified_param": str})
        def do_something_simplified(config_in: DoSomethingSimplifiedConfig): ...


def test_config_annotation_extra_param_err() -> None:
    class DoSomethingConfig(Config):
        config_param: str

    @op
    def do_something(config: DoSomethingConfig) -> str:
        return config.config_param

    class DoSomethingSimplifiedConfig(Config):
        simplified_param: str

    # Ensure that we error if the @configured function has an extra param
    with pytest.raises(
        CheckError,
        match="@configured function should have exactly one parameter",
    ):

        @configured(do_something)
        def do_something_simplified(config_in: DoSomethingSimplifiedConfig, useless_param: str): ...
