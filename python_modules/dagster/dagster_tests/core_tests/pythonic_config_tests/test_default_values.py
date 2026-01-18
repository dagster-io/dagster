import dagster as dg
import pytest


def test_default_values():
    class ANewConfigOpConfig(dg.Config):
        a_string: str = "bar"
        an_int: int = 2

    executed = {}

    @dg.op
    def a_struct_config_op(config: ANewConfigOpConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["yes"] = True

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    @dg.job
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

    @dg.op
    def a_primitive_config_op(config: str = "foo"):
        assert config == "foo"
        executed["yes"] = True

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_primitive_config_op).has_config_arg()

    @dg.job
    def a_job():
        a_primitive_config_op()

    assert a_job

    a_job.execute_in_process()

    with pytest.raises(AssertionError):
        a_job.execute_in_process({"ops": {"a_primitive_config_op": {"config": "qux"}}})

    assert executed["yes"]


def test_direct_op_invocation_default():
    class MyBasicOpConfig(dg.Config):
        foo: str = "qux"

    @dg.op
    def basic_op(context, config: MyBasicOpConfig):
        assert config.foo == "bar"

    with pytest.raises(AssertionError):
        basic_op(dg.build_op_context())

    basic_op(dg.build_op_context(op_config={"foo": "bar"}))

    @dg.op
    def primitive_config_op(context, config: str = "bar"):
        assert config == "bar"

    with pytest.raises(AssertionError):
        primitive_config_op(dg.build_op_context(op_config="qux"))

    primitive_config_op(dg.build_op_context())


def test_default_values_nested():
    class ANestedOpConfig(dg.Config):
        an_int: int = 1
        a_bool: bool = True

    class AnotherNestedOpConfig(dg.Config):
        a_float: float = 1.0

    class AnOpConfig(dg.Config):
        a_string: str = "bar"
        a_nested: ANestedOpConfig
        another_nested: AnotherNestedOpConfig = AnotherNestedOpConfig()

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        assert config.a_string == "foo"
        assert config.a_nested.an_int == 2
        assert config.a_nested.a_bool is True
        assert config.another_nested.a_float == 1.0
        executed["yes"] = True

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string": "foo", "a_nested": {"an_int": 2}}}}}
    )

    assert executed["yes"]


def test_default_values_extension() -> None:
    class BaseConfig(dg.Config):
        a_string: str = "bar"
        an_int: int = 2

    class ExtendingConfig(BaseConfig):
        a_float: float = 1.0

    executed = {}

    @dg.op
    def a_struct_config_op(config: ExtendingConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        assert config.a_float == 1.0
        executed["yes"] = True

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job

    with pytest.raises(AssertionError):
        # ensure that assertion-raising default value is passed
        a_job.execute_in_process()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"a_string": "foo"}}}})

    assert executed["yes"]


def test_default_values_nested_override():
    class InnermostConfig(dg.Config):
        a_float: float = 1.0
        another_float: float = 2.0

    class ANestedOpConfig(dg.Config):
        an_int: int = 1
        a_bool: bool = True
        inner_config: InnermostConfig = InnermostConfig(another_float=1.0)

    class AnOpConfig(dg.Config):
        a_string: str = "foo"
        a_nested: ANestedOpConfig = ANestedOpConfig(an_int=5)

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        assert config.a_string == "foo"
        assert config.a_nested.an_int == 5
        assert config.a_nested.a_bool is True
        assert config.a_nested.inner_config.a_float == 3.0
        assert config.a_nested.inner_config.another_float == 1.0
        executed["yes"] = True

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {"a_string": "foo", "a_nested": {"inner_config": {"a_float": 3.0}}}
                }
            }
        }
    )

    assert executed["yes"]
