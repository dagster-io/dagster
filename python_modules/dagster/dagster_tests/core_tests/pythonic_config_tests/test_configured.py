from typing import Any, Dict

from dagster import (
    Config,
    RunConfig,
    configured,
    job,
    op,
)


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
    def do_something_simplified(config_in: DoSomethingSimplifiedConfig) -> Dict[str, Any]:
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
