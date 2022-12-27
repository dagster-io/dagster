import sys

import pytest
from pydantic import BaseModel

from dagster import AssetOut
from dagster import _check as check
from dagster import asset, job, multi_asset, op, validate_run_config
from dagster._config.config_type import ConfigTypeKind
from dagster._config.field_utils import convert_potential_field
from dagster._config.source import BoolSource, IntSource, StringSource
from dagster._config.structured_config import Config, infer_schema_from_config_class
from dagster._config.type_printer import print_config_type_to_string
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.errors import DagsterInvalidConfigDefinitionError, DagsterInvalidConfigError
from dagster._core.execution.context.invocation import build_op_context
from dagster._legacy import pipeline
from dagster._utils.cached_method import cached_method


def test_disallow_config_schema_conflict():
    class ANewConfigOpConfig(Config):
        a_string: str

    with pytest.raises(check.ParameterCheckError):

        @op(config_schema=str)
        def a_double_config(config: ANewConfigOpConfig):
            pass


def test_infer_config_schema():
    old_schema = {"a_string": StringSource, "an_int": IntSource}

    class ConfigClassTest(Config):
        a_string: str
        an_int: int

    assert type_string_from_config_schema(old_schema) == type_string_from_pydantic(ConfigClassTest)

    from_old_schema_field = convert_potential_field(old_schema)
    config_class_config_field = infer_schema_from_config_class(ConfigClassTest)

    assert type_string_from_config_schema(
        from_old_schema_field.config_type
    ) == type_string_from_config_schema(config_class_config_field)


def type_string_from_config_schema(config_schema):
    return print_config_type_to_string(convert_potential_field(config_schema).config_type)


def type_string_from_pydantic(cls):
    return print_config_type_to_string(infer_schema_from_config_class(cls).config_type)


def test_decorated_op_function():
    class ANewConfigOpConfig(Config):
        a_string: str

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        pass

    @op(config_schema={"a_string": str})
    def an_old_config_op():
        pass

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert not DecoratedOpFunction(an_old_config_op).has_config_arg()
    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    config_param = DecoratedOpFunction(a_struct_config_op).get_config_arg()
    assert config_param.name == "config"


def test_struct_config():
    class ANewConfigOpConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_struct_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE
    assert list(a_struct_config_op.config_schema.config_type.fields.keys()) == [
        "a_string",
        "an_int",
    ]

    @job
    def a_job():
        a_struct_config_op()

    assert a_job

    from dagster._core.errors import DagsterInvalidConfigError

    with pytest.raises(DagsterInvalidConfigError):
        # ensure that config schema actually works
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"a_string_mispelled": "foo", "an_int": 2}}}}
        )

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string": "foo", "an_int": 2}}}}
    )

    assert executed["yes"]


def test_with_assets():
    class AnAssetConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @asset
    def my_asset(config: AnAssetConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["yes"] = True

    assert (
        build_assets_job(
            "blah",
            [my_asset],
            config={"ops": {"my_asset": {"config": {"a_string": "foo", "an_int": 2}}}},
        )
        .execute_in_process()
        .success
    )

    assert executed["yes"]


def test_multi_asset():
    class AMultiAssetConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @multi_asset(outs={"a": AssetOut(key="asset_a"), "b": AssetOut(key="asset_b")})
    def two_assets(config: AMultiAssetConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["yes"] = True
        return 1, 2

    assert (
        build_assets_job(
            "blah",
            [two_assets],
            config={"ops": {"two_assets": {"config": {"a_string": "foo", "an_int": 2}}}},
        )
        .execute_in_process()
        .success
    )

    assert executed["yes"]


def test_primitive_struct_config():

    executed = {}

    @op
    def a_str_op(config: str):
        executed["yes"] = True
        assert config == "foo"

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_str_op).has_config_arg()

    @job
    def a_job():
        a_str_op()

    assert a_job

    from dagster._core.errors import DagsterInvalidConfigError

    with pytest.raises(DagsterInvalidConfigError):
        # ensure that config schema actually works
        a_job.execute_in_process({"ops": {"a_str_op": {"config": 1}}})

    a_job.execute_in_process({"ops": {"a_str_op": {"config": "foo"}}})

    assert executed["yes"]

    @op
    def a_bool_op(config: bool):
        assert not config

    @op
    def a_int_op(config: int):
        assert config == 1

    @op
    def a_dict_op(config: dict):
        assert config == {"foo": 1}

    @op
    def a_list_op(config: list):
        assert config == [1, 2, 3]

    @job
    def a_larger_job():
        a_str_op()
        a_bool_op()
        a_int_op()
        a_dict_op()
        a_list_op()

    a_larger_job.execute_in_process(
        {
            "ops": {
                "a_str_op": {"config": "foo"},
                "a_bool_op": {"config": False},
                "a_int_op": {"config": 1},
                "a_dict_op": {"config": {"foo": 1}},
                "a_list_op": {"config": [1, 2, 3]},
            }
        }
    )


def test_invalid_struct_config():
    # Config should extend Config, not BaseModel
    with pytest.raises(DagsterInvalidConfigDefinitionError):

        class BaseModelExtendingConfig(BaseModel):
            a_string: str
            an_int: int

        @op
        def a_basemodel_config_op(config: BaseModelExtendingConfig):
            pass


def test_nested_struct_config():
    class ANestedConfig(Config):
        a_string: str
        an_int: int

    class ANewConfigOpConfig(Config):
        a_nested_value: ANestedConfig
        a_bool: bool

    executed = {}

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_nested_value.a_string == "foo"
        assert config.a_nested_value.an_int == 2
        assert config.a_bool == True

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_struct_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE
    assert list(a_struct_config_op.config_schema.config_type.fields.keys()) == [
        "a_nested_value",
        "a_bool",
    ]

    @job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {"a_bool": True, "a_nested_value": {"a_string": "foo", "an_int": 2}}
                }
            }
        }
    )

    assert executed["yes"]


def test_direct_op_invocation():
    class MyBasicOpConfig(Config):
        foo: str

    # Limitation: for now direct invocation still requires the op to have a context argument.
    @op
    def basic_op(context, config: MyBasicOpConfig):
        assert config.foo == "bar"

    basic_op(build_op_context(op_config={"foo": "bar"}))

    with pytest.raises(AssertionError):
        basic_op(build_op_context(op_config={"foo": "qux"}))

    with pytest.raises(DagsterInvalidConfigError):
        basic_op(build_op_context(op_config={"baz": "qux"}))


def test_validate_run_config():
    class MyBasicOpConfig(Config):
        foo: str

    @op()
    def requires_config(config: MyBasicOpConfig):
        pass

    @pipeline
    def pipeline_requires_config():
        requires_config()

    result = validate_run_config(
        pipeline_requires_config, {"solids": {"requires_config": {"config": {"foo": "bar"}}}}
    )

    assert result == {
        "solids": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {"in_process": {"retries": {"enabled": {}}}},
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    result_with_storage = validate_run_config(
        pipeline_requires_config,
        {"solids": {"requires_config": {"config": {"foo": "bar"}}}},
    )

    assert result_with_storage == {
        "solids": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {"in_process": {"retries": {"enabled": {}}}},
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    with pytest.raises(DagsterInvalidConfigError):
        validate_run_config(pipeline_requires_config)


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python3.8")
def test_cached_property():
    from functools import cached_property

    counts = {
        "plus": 0,
        "mult": 0,
    }

    class SomeConfig(Config):
        x: int
        y: int

        @cached_property
        def plus(self):
            counts["plus"] += 1
            return self.x + self.y

        @cached_property
        def mult(self):
            counts["mult"] += 1
            return self.x * self.y

    config = SomeConfig(x=3, y=5)

    assert counts["plus"] == 0
    assert counts["mult"] == 0

    assert config.plus == 8

    assert counts["plus"] == 1
    assert counts["mult"] == 0

    assert config.plus == 8

    assert counts["plus"] == 1
    assert counts["mult"] == 0

    assert config.mult == 15

    assert counts["plus"] == 1
    assert counts["mult"] == 1


def test_cached_method():
    counts = {
        "plus": 0,
        "mult": 0,
    }

    class SomeConfig(Config):
        x: int
        y: int

        @cached_method
        def plus(self):
            counts["plus"] += 1
            return self.x + self.y

        @cached_method
        def mult(self):
            counts["mult"] += 1
            return self.x * self.y

    config = SomeConfig(x=3, y=5)

    assert counts["plus"] == 0
    assert counts["mult"] == 0

    assert config.plus() == 8

    assert counts["plus"] == 1
    assert counts["mult"] == 0

    assert config.plus() == 8

    assert counts["plus"] == 1
    assert counts["mult"] == 0

    assert config.mult() == 15

    assert counts["plus"] == 1
    assert counts["mult"] == 1


def test_string_source_default():
    class RawStringConfigSchema(Config):
        a_str: str

    assert print_config_type_to_string({"a_str": StringSource}) == print_config_type_to_string(
        infer_schema_from_config_class(RawStringConfigSchema).config_type
    )


def test_bool_source_default():
    class RawBoolConfigSchema(Config):
        a_bool: bool

    assert print_config_type_to_string({"a_bool": BoolSource}) == print_config_type_to_string(
        infer_schema_from_config_class(RawBoolConfigSchema).config_type
    )


def test_int_source_default():
    class RawIntConfigSchema(Config):
        an_int: int

    assert print_config_type_to_string({"an_int": IntSource}) == print_config_type_to_string(
        infer_schema_from_config_class(RawIntConfigSchema).config_type
    )
