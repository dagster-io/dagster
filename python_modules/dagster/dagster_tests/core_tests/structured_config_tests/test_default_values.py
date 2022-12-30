import pytest
from pydantic import BaseModel

from dagster import _check as check
from dagster import job, op, validate_run_config
from dagster._config.config_type import ConfigTypeKind
from dagster._config.field_utils import convert_potential_field
from dagster._config.structured_config import Config, infer_schema_from_config_class
from dagster._core.errors import DagsterInvalidConfigDefinitionError, DagsterInvalidConfigError
from dagster._core.execution.context.invocation import build_op_context
from dagster._legacy import pipeline


def test_default_values():
    class ANewConfigOpConfig(Config):
        a_string: str = "bar"
        an_int: int = 2

    executed = {}

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["yes"] = True

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    @job
    def a_job():
        a_struct_config_op()

    assert a_job

    with pytest.raises(AssertionError):
        # ensure that assertion-raising default value is passed
        a_job.execute_in_process()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"a_string": "foo"}}}})

    assert executed["yes"]


def test_default_value_primitive():
    executed = {}

    @op
    def a_primitive_config_op(config: str = "foo"):
        assert config == "foo"
        executed["yes"] = True

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_primitive_config_op).has_config_arg()

    @job
    def a_job():
        a_primitive_config_op()

    assert a_job

    a_job.execute_in_process()

    with pytest.raises(AssertionError):
        a_job.execute_in_process({"ops": {"a_primitive_config_op": {"config": "qux"}}})

    assert executed["yes"]


def test_direct_op_invocation_default():
    class MyBasicOpConfig(Config):
        foo: str = "qux"

    @op
    def basic_op(context, config: MyBasicOpConfig):
        assert config.foo == "bar"

    with pytest.raises(AssertionError):
        basic_op(build_op_context())

    basic_op(build_op_context(op_config={"foo": "bar"}))

    @op
    def primitive_config_op(context, config: str = "bar"):
        assert config == "bar"

    with pytest.raises(AssertionError):
        primitive_config_op(build_op_context(op_config="qux"))

    primitive_config_op(build_op_context())


def test_default_values_nested():
    class ANestedOpConfig(Config):
        an_int: int = 1
        a_bool: bool = True

    class AnotherNestedOpConfig(Config):
        a_float: float = 1.0

    class AnOpConfig(Config):
        a_string: str = "bar"
        a_nested: ANestedOpConfig
        another_nested: AnotherNestedOpConfig

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        assert config.a_string == "foo"
        assert config.a_nested.an_int == 2
        assert config.a_nested.a_bool is True
        assert config.another_nested.a_float == 1.0
        executed["yes"] = True

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    @job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string": "foo", "a_nested": {"an_int": 2}}}}}
    )

    assert executed["yes"]
