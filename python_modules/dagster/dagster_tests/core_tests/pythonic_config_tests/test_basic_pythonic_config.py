import sys
from typing import List, Optional

import dagster
import pydantic
import pytest
from dagster import (
    AssetOut,
    EnvVar,
    _check as check,
    asset,
    job,
    materialize,
    multi_asset,
    op,
    validate_run_config,
)
from dagster._config.config_type import ConfigTypeKind, Noneable
from dagster._config.field_utils import convert_potential_field
from dagster._config.pythonic_config import Config, infer_schema_from_config_class
from dagster._config.source import BoolSource, IntSource, StringSource
from dagster._config.type_printer import print_config_type_to_string
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.run_config import RunConfig
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidInvocationError,
    DagsterInvalidPythonicConfigDefinitionError,
)
from dagster._core.execution.context.invocation import build_op_context
from dagster._core.test_utils import environ
from dagster._utils.cached_method import cached_method
from pydantic import (
    BaseModel,
    Field as PyField,
)


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

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

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

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

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

    assert materialize(
        [my_asset],
        run_config={
            "ops": {
                "my_asset": {
                    "config": {"a_string": "foo", "an_int": 2},
                },
            },
        },
    ).success

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

    assert materialize(
        [two_assets],
        run_config={"ops": {"two_assets": {"config": {"a_string": "foo", "an_int": 2}}}},
    ).success

    assert executed["yes"]


def test_primitive_struct_config():
    executed = {}

    @op
    def a_str_op(config: str):
        executed["yes"] = True
        assert config == "foo"

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

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
    with pytest.raises(DagsterInvalidPythonicConfigDefinitionError):

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
        assert config.a_bool is True

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

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


def test_direct_op_invocation() -> None:
    class MyBasicOpConfig(Config):
        foo: str

    @op
    def basic_op(context, config: MyBasicOpConfig):
        assert config.foo == "bar"

    basic_op(build_op_context(op_config={"foo": "bar"}))

    with pytest.raises(AssertionError):
        basic_op(build_op_context(op_config={"foo": "qux"}))

    with pytest.raises(DagsterInvalidConfigError):
        basic_op(build_op_context(op_config={"baz": "qux"}))

    @op
    def basic_op_no_context(config: MyBasicOpConfig):
        assert config.foo == "bar"

    basic_op_no_context(build_op_context(op_config={"foo": "bar"}))

    with pytest.raises(AssertionError):
        basic_op_no_context(build_op_context(op_config={"foo": "qux"}))

    with pytest.raises(DagsterInvalidConfigError):
        basic_op_no_context(build_op_context(op_config={"baz": "qux"}))


def test_direct_op_invocation_complex_config() -> None:
    class MyBasicOpConfig(Config):
        foo: str
        bar: bool
        baz: int
        qux: List[str]

    @op
    def basic_op(context, config: MyBasicOpConfig):
        assert config.foo == "bar"

    basic_op(build_op_context(op_config={"foo": "bar", "bar": True, "baz": 1, "qux": ["a", "b"]}))

    with pytest.raises(AssertionError):
        basic_op(
            build_op_context(op_config={"foo": "qux", "bar": True, "baz": 1, "qux": ["a", "b"]})
        )

    with pytest.raises(DagsterInvalidConfigError):
        basic_op(
            build_op_context(op_config={"foo": "bar", "bar": "true", "baz": 1, "qux": ["a", "b"]})
        )

    @op
    def basic_op_no_context(config: MyBasicOpConfig):
        assert config.foo == "bar"

    basic_op_no_context(
        build_op_context(op_config={"foo": "bar", "bar": True, "baz": 1, "qux": ["a", "b"]})
    )

    with pytest.raises(AssertionError):
        basic_op_no_context(
            build_op_context(op_config={"foo": "qux", "bar": True, "baz": 1, "qux": ["a", "b"]})
        )

    with pytest.raises(DagsterInvalidConfigError):
        basic_op_no_context(
            build_op_context(op_config={"foo": "bar", "bar": "true", "baz": 1, "qux": ["a", "b"]})
        )


def test_validate_run_config():
    class MyBasicOpConfig(Config):
        foo: str

    @op()
    def requires_config(config: MyBasicOpConfig):
        pass

    @job
    def job_requires_config():
        requires_config()

    result = validate_run_config(
        job_requires_config, {"ops": {"requires_config": {"config": {"foo": "bar"}}}}
    )

    assert result == {
        "ops": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {
            "multi_or_in_process_executor": {
                "multiprocess": {"max_concurrent": None, "retries": {"enabled": {}}}
            }
        },
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    result_with_runconfig = validate_run_config(
        job_requires_config, RunConfig(ops={"requires_config": {"config": {"foo": "bar"}}})
    )
    assert result_with_runconfig == result

    result_with_structured_in = validate_run_config(
        job_requires_config, RunConfig(ops={"requires_config": MyBasicOpConfig(foo="bar")})
    )
    assert result_with_structured_in == result

    result_with_dict_config = validate_run_config(
        job_requires_config,
        {"ops": {"requires_config": {"config": {"foo": "bar"}}}},
    )

    assert result_with_dict_config == {
        "ops": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {
            "multi_or_in_process_executor": {
                "multiprocess": {"max_concurrent": None, "retries": {"enabled": {}}}
            }
        },
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    with pytest.raises(DagsterInvalidConfigError):
        validate_run_config(job_requires_config)


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


def test_string_source_default_directly_on_op():
    @op
    def op_with_raw_str_config(config: str):
        raise Exception("not called")

    assert isinstance(op_with_raw_str_config, OpDefinition)
    assert op_with_raw_str_config.config_field
    assert op_with_raw_str_config.config_field.config_type is StringSource


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


def test_optional_string_source_default() -> None:
    class RawStringConfigSchema(Config):
        a_str: Optional[str]

    assert print_config_type_to_string(
        {"a_str": dagster.Field(Noneable(StringSource))}
    ) == print_config_type_to_string(
        infer_schema_from_config_class(RawStringConfigSchema).config_type
    )

    assert RawStringConfigSchema(a_str=None).a_str is None


def test_optional_string_source_with_default_none() -> None:
    class RawStringConfigSchema(Config):
        a_str: Optional[str] = None

    assert print_config_type_to_string(
        {"a_str": dagster.Field(Noneable(StringSource))}
    ) == print_config_type_to_string(
        infer_schema_from_config_class(RawStringConfigSchema).config_type
    )

    assert RawStringConfigSchema().a_str is None
    assert RawStringConfigSchema(a_str=None).a_str is None


def test_optional_bool_source_default() -> None:
    class RawBoolConfigSchema(Config):
        a_bool: Optional[bool]

    assert print_config_type_to_string(
        {"a_bool": dagster.Field(Noneable(BoolSource))}
    ) == print_config_type_to_string(
        infer_schema_from_config_class(RawBoolConfigSchema).config_type
    )


def test_optional_int_source_default() -> None:
    class OptionalInt(Config):
        an_int: Optional[int]

    assert print_config_type_to_string(
        {"an_int": dagster.Field(Noneable(IntSource))}
    ) == print_config_type_to_string(infer_schema_from_config_class(OptionalInt).config_type)


def test_schema_aliased_field():
    # schema is a common config element and you cannot use it in pydantic without an alias
    class ConfigWithSchema(Config):
        schema_: str = pydantic.Field(alias="schema")

    # use the alias in the constructor
    obj = ConfigWithSchema(schema="foo")
    # actual field name to access
    assert obj.schema_ == "foo"

    # show different pydantic methods
    assert obj.dict() == {"schema_": "foo"}
    assert obj.dict(by_alias=True) == {"schema": "foo"}

    # we respect the alias in the config space
    assert print_config_type_to_string(
        {"schema": dagster.Field(StringSource)}
    ) == print_config_type_to_string(infer_schema_from_config_class(ConfigWithSchema).config_type)

    executed = {}

    @op
    def an_op(context, config: ConfigWithSchema):
        # use the raw property in python space
        assert config.schema_ == "bar"
        # use the alias in config space
        assert context.op_config == {"schema": "bar"}
        executed["yes"] = True

    @job
    def a_job():
        an_op()

    # use the alias in config space
    assert a_job.execute_in_process({"ops": {"an_op": {"config": {"schema": "bar"}}}}).success
    assert executed["yes"]


def test_env_var():
    with environ({"ENV_VARIABLE_FOR_TEST_INT": "2", "ENV_VARIABLE_FOR_TEST": "foo"}):

        class AnAssetConfig(Config):
            a_string: str
            an_int: int

        executed = {}

        @asset
        def my_asset(config: AnAssetConfig):
            assert config.a_string == "foo"
            assert config.an_int == 2
            executed["yes"] = True

        assert materialize(
            [my_asset],
            run_config={
                "ops": {
                    "my_asset": {
                        "config": {
                            "a_string": {"env": "ENV_VARIABLE_FOR_TEST"},
                            "an_int": {"env": "ENV_VARIABLE_FOR_TEST_INT"},
                        }
                    }
                }
            },
        ).success

        assert executed["yes"]


def test_structured_run_config_ops():
    class ANewConfigOpConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    @job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        RunConfig(ops={"a_struct_config_op": ANewConfigOpConfig(a_string="foo", an_int=2)})
    )
    assert executed["yes"]


def test_structured_run_config_optional() -> None:
    class ANewConfigOpConfig(Config):
        a_string: Optional[str]
        an_int: Optional[int] = None
        a_float: float = PyField(None)

    executed = {}

    @op
    def a_struct_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_string is None
        assert config.an_int is None
        assert config.a_float is None

    @job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        RunConfig(ops={"a_struct_config_op": ANewConfigOpConfig(a_string=None)})  # type: ignore
    )
    assert executed["yes"]


def test_structured_run_config_multi_asset():
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

    assert materialize(
        [two_assets],
        run_config=RunConfig(ops={"two_assets": AMultiAssetConfig(a_string="foo", an_int=2)}),
    ).success


def test_structured_run_config_assets():
    class AnAssetConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @asset
    def my_asset(config: AnAssetConfig):
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["yes"] = True

    assert materialize(
        [my_asset],
        run_config=RunConfig(
            ops={
                "my_asset": AnAssetConfig(a_string="foo", an_int=2),
            }
        ),
    ).success
    assert executed["yes"]

    # define_asset_job
    del executed["yes"]
    my_asset_job = define_asset_job(
        "my_asset_job",
        selection="my_asset",
        config=RunConfig(
            ops={
                "my_asset": AnAssetConfig(a_string="foo", an_int=2),
            }
        ),
    )
    defs = Definitions(
        assets=[my_asset],
        jobs=[my_asset_job],
    )
    defs.get_job_def("my_asset_job").execute_in_process()
    assert executed["yes"]

    # materialize
    del executed["yes"]
    asset_result = materialize(
        [my_asset],
        run_config=RunConfig(
            ops={
                "my_asset": AnAssetConfig(a_string="foo", an_int=2),
            }
        ),
    )
    assert asset_result.success
    assert executed["yes"]


def test_structured_run_config_assets_optional() -> None:
    class AnAssetConfig(Config):
        a_string: str = PyField(None)
        an_int: Optional[int] = None

    executed = {}

    @asset
    def my_asset(config: AnAssetConfig):
        assert config.a_string is None
        assert config.an_int is None
        executed["yes"] = True

    # materialize
    asset_result = materialize(
        [my_asset],
        run_config=RunConfig(
            ops={
                "my_asset": AnAssetConfig(),  # type: ignore
            }
        ),
    )
    assert asset_result.success
    assert executed["yes"]


def test_direct_op_invocation_plain_arg_with_config() -> None:
    class MyConfig(Config):
        num: int

    executed = {}

    @op
    def an_op(config: MyConfig) -> None:
        assert config.num == 1
        executed["yes"] = True

    an_op(MyConfig(num=1))

    assert executed["yes"]


def test_direct_op_invocation_kwarg_with_config() -> None:
    class MyConfig(Config):
        num: int

    executed = {}

    @op
    def an_op(config: MyConfig) -> None:
        assert config.num == 1
        executed["yes"] = True

    an_op(config=MyConfig(num=1))

    assert executed["yes"]


def test_direct_op_invocation_arg_complex() -> None:
    class MyConfig(Config):
        num: int

    class MyOuterConfig(Config):
        inner: MyConfig
        string: str

    executed = {}

    @op
    def an_op(config: MyOuterConfig) -> None:
        assert config.inner.num == 1
        assert config.string == "foo"
        executed["yes"] = True

    an_op(MyOuterConfig(inner=MyConfig(num=1), string="foo"))

    assert executed["yes"]


def test_direct_op_invocation_kwarg_complex() -> None:
    class MyConfig(Config):
        num: int

    class MyOuterConfig(Config):
        inner: MyConfig
        string: str

    executed = {}

    @op
    def an_op(config: MyOuterConfig) -> None:
        assert config.inner.num == 1
        assert config.string == "foo"
        executed["yes"] = True

    an_op(config=MyOuterConfig(inner=MyConfig(num=1), string="foo"))

    assert executed["yes"]


def test_direct_op_invocation_kwarg_very_complex() -> None:
    class MyConfig(Config):
        num: int

    class MyOuterConfig(Config):
        inner: MyConfig
        string: str

    class MyOutermostConfig(Config):
        inner: MyOuterConfig
        boolean: bool

    executed = {}

    @op
    def an_op(config: MyOutermostConfig) -> None:
        assert config.inner.inner.num == 2
        assert config.inner.string == "foo"
        assert config.boolean is False
        executed["yes"] = True

    with environ({"ENV_VARIABLE_FOR_TEST_INT": "2"}):
        an_op(
            config=MyOutermostConfig(
                inner=MyOuterConfig(
                    inner=MyConfig(num=EnvVar.int("ENV_VARIABLE_FOR_TEST_INT")), string="foo"
                ),
                boolean=False,
            )
        )

    assert executed["yes"]


def test_direct_asset_invocation_plain_arg_with_config() -> None:
    class MyConfig(Config):
        num: int

    executed = {}

    @asset
    def an_asset(config: MyConfig) -> None:
        assert config.num == 1
        executed["yes"] = True

    an_asset(MyConfig(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_kwarg_with_config() -> None:
    class MyConfig(Config):
        num: int

    executed = {}

    @asset
    def an_asset(config: MyConfig) -> None:
        assert config.num == 1
        executed["yes"] = True

    an_asset(config=MyConfig(num=1))

    assert executed["yes"]


def test_direct_op_invocation_kwarg_with_config_and_context() -> None:
    class MyConfig(Config):
        num: int

    executed = {}

    @op
    def an_op(context, config: MyConfig) -> None:
        assert config.num == 1
        executed["yes"] = True

    an_op(context=build_op_context(), config=MyConfig(num=1))
    assert executed["yes"]


def test_direct_op_invocation_kwarg_with_config_and_context_err() -> None:
    class MyConfig(Config):
        num: int

    executed = {}

    @op
    def an_op(context, config: MyConfig) -> None:
        assert config.num == 1
        executed["yes"] = True

    with pytest.raises(
        DagsterInvalidInvocationError, match="Cannot provide config in both context and kwargs"
    ):
        an_op(context=build_op_context(config={"num": 2}), config=MyConfig(num=1))


def test_truthy_and_falsey_defaults() -> None:
    class ConfigClassToConvertTrue(Config):
        bool_with_default_true_value: bool = PyField(default=True)

    fields = ConfigClassToConvertTrue.to_fields_dict()
    true_default_field = fields["bool_with_default_true_value"]
    assert true_default_field.is_required is False
    assert true_default_field.default_provided is True
    assert true_default_field.default_value is True

    class ConfigClassToConvertFalse(Config):
        bool_with_default_false_value: bool = PyField(default=False)

    fields = ConfigClassToConvertFalse.to_fields_dict()
    false_default_field = fields["bool_with_default_false_value"]
    assert false_default_field.is_required is False
    assert false_default_field.default_provided is True
    assert false_default_field.default_value is False


def execution_run_config() -> None:
    from dagster import RunConfig, job, op

    @op
    def foo_op():
        pass

    @job
    def foo_job():
        foo_op()

    result = foo_job.execute_in_process(
        run_config=RunConfig(
            execution={"config": {"multiprocess": {"config": {"max_concurrent": 0}}}}
        ),
    )
    assert result.success


def test_run_config_equality() -> None:
    config_dict = {
        "ops": {
            "foo_op": {
                "config": {"foo": "bar"},
            },
        },
        "execution": {
            "multiprocess": {
                "config": {"max_concurrent": 0},
            },
        },
    }
    assert RunConfig(config_dict) == RunConfig(config_dict)
