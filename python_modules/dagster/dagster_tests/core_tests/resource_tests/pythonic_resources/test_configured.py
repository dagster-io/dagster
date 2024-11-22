from typing import Any, Dict

import pytest
from dagster import Config, ConfigurableResource, InitResourceContext, configured, job, op, resource
from dagster._check import CheckError


def test_config_mapping_return_resource_config_dict_noargs() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    @configured(MyResource)
    def my_resource_noargs(_) -> dict[str, Any]:
        return {"resource_param": "foo"}

    @op
    def do_something(my_resource: ConfigurableResource) -> str:
        return my_resource.resource_param

    @job
    def do_it_all() -> None:
        do_something()

    result = do_it_all.execute_in_process(resources={"my_resource": my_resource_noargs})
    assert result.success
    assert result.output_for_node("do_something") == "foo"


def test_config_mapping_return_resource_config_dict() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    @resource(config_schema={"resource_param": str})
    def my_resource_legacy(context: InitResourceContext) -> MyResource:
        return MyResource(resource_param=context.resource_config["resource_param"])

    @configured(my_resource_legacy, config_schema={"simplified_param": str})
    def my_resource_legacy_simplified(config_in) -> dict[str, Any]:
        return {"resource_param": config_in["simplified_param"]}

    @op
    def do_something(my_resource: ConfigurableResource) -> str:
        return my_resource.resource_param

    @job
    def do_it_all() -> None:
        do_something()

    result = do_it_all.execute_in_process(
        resources={
            "my_resource": my_resource_legacy_simplified.configured({"simplified_param": "foo"})
        }
    )
    assert result.success
    assert result.output_for_node("do_something") == "foo"

    class MyResourceSimplifiedConfig(Config):
        simplified_param: str

    # New, fancy config mapping takes in a Pythonic config object but returns normal config dict
    @configured(MyResource)
    def my_resource_simplified(config_in: MyResourceSimplifiedConfig) -> dict[str, Any]:
        return {"resource_param": config_in.simplified_param}

    result = do_it_all.execute_in_process(
        resources={"my_resource": my_resource_simplified.configured({"simplified_param": "foo"})}
    )
    assert result.success
    assert result.output_for_node("do_something") == "foo"


def test_config_mapping_return_resource_object() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    @op
    def do_something(my_resource: ConfigurableResource) -> str:
        return my_resource.resource_param

    @job
    def do_it_all() -> None:
        do_something()

    class MyResourceSimplifiedConfig(Config):
        simplified_param: str

    # New, fancy config mapping takes in a Pythonic config object and returns a constructed resource
    @configured(MyResource)
    def my_resource_simplified(config_in: MyResourceSimplifiedConfig) -> MyResource:
        return MyResource(resource_param=config_in.simplified_param)

    result = do_it_all.execute_in_process(
        resources={"my_resource": my_resource_simplified.configured({"simplified_param": "foo"})}
    )
    assert result.success
    assert result.output_for_node("do_something") == "foo"


def test_config_annotation_no_config_schema_err() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    class MyResourceSimplifiedConfig(Config):
        simplified_param: str

    # Ensure that we error if we try to provide a config_schema to a @configured function
    # which has a Config-annotated param - no need to provide a config_schema in this case
    with pytest.raises(
        CheckError,
        match="Cannot provide config_schema to @configured function with Config-annotated param",
    ):

        @configured(MyResource, config_schema={"simplified_param": str})
        def my_resource_simplified(config_in: MyResourceSimplifiedConfig): ...


def test_config_annotation_extra_param_err() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    class MyResourceSimplifiedConfig(Config):
        simplified_param: str

    # Ensure that we error if the @configured function has an extra param
    with pytest.raises(
        CheckError,
        match="@configured function should have exactly one parameter",
    ):

        @configured(MyResource)
        def my_resource_simplified(config_in: MyResourceSimplifiedConfig, useless_param: str): ...


def test_factory_resource_pattern_noargs() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    class MyResourceNoargs(ConfigurableResource):
        def create_resource(self, context: InitResourceContext) -> Any:
            return MyResource(resource_param="foo")

    @op
    def do_something(my_resource: ConfigurableResource) -> str:
        return my_resource.resource_param

    @job
    def do_it_all() -> None:
        do_something()

    result = do_it_all.execute_in_process(resources={"my_resource": MyResourceNoargs()})
    assert result.success
    assert result.output_for_node("do_something") == "foo"


def test_factory_resource_pattern_args() -> None:
    class MyResource(ConfigurableResource):
        resource_param: str

    class MyResourceFromInt(ConfigurableResource):
        an_int: int

        def create_resource(self, context: InitResourceContext) -> Any:
            return MyResource(resource_param=str(self.an_int))

    @op
    def do_something(my_resource: ConfigurableResource) -> str:
        return my_resource.resource_param

    @job
    def do_it_all() -> None:
        do_something()

    result = do_it_all.execute_in_process(resources={"my_resource": MyResourceFromInt(an_int=10)})
    assert result.success
    assert result.output_for_node("do_something") == "10"
