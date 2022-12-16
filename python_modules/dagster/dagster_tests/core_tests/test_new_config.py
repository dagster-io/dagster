from typing import Dict, List, Mapping, Union
from dagster._config.config_type import ConfigTypeKind
import pytest
from pydantic import BaseModel, Extra, Field

from dagster import OpExecutionContext
from dagster import _check as check
from dagster import job, op
from dagster._config.field_utils import convert_potential_field
from dagster._config.pydantic_config import infer_config_field_from_pydanic


def test_old_config():

    executed = {}

    @op(config_schema={"a_string": str})
    def a_new_config_op(context: OpExecutionContext):
        assert context.op_config["a_string"] == "foo"
        executed["yes"] = True
        pass

    @job
    def a_job():
        a_new_config_op()

    a_job.execute_in_process({"ops": {"a_new_config_op": {"config": {"a_string": "foo"}}}})

    assert executed["yes"]

    print(a_new_config_op.config_schema)


def test_disallow_config_schema_conflict():
    class ANewConfigOpConfig(BaseModel):
        a_string: str

    with pytest.raises(check.ParameterCheckError):

        @op(config_schema=str)
        def a_double_config(config: ANewConfigOpConfig):
            pass


from dagster._config.type_printer import print_config_type_to_string


def test_infer_config_schema():
    assert infer_config_field_from_pydanic
    config_field = infer_config_field_from_pydanic(str)
    assert config_field.config_type.given_name == "String"

    from_old_schema_field = convert_potential_field({"a_string": str, "an_int": int})
    assert from_old_schema_field
    print(print_config_type_to_string(from_old_schema_field.config_type))

    class ConfigClassTest(BaseModel):
        a_string: str
        an_int: int

    config_class_config_field = infer_config_field_from_pydanic(ConfigClassTest)

    print(print_config_type_to_string(config_class_config_field.config_type))

    assert type_string_from_config_schema(
        {"a_string": str, "an_int": int}
    ) == type_string_from_pydantic(ConfigClassTest)


def type_string_from_config_schema(config_schema):
    return print_config_type_to_string(convert_potential_field(config_schema).config_type)


def type_string_from_pydantic(cls):
    return print_config_type_to_string(infer_config_field_from_pydanic(cls).config_type)


def test_decorated_solid_function():
    class ANewConfigOpConfig(BaseModel):
        a_string: str

    @op
    def a_new_config_op(config: ANewConfigOpConfig):
        pass

    from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction

    assert DecoratedSolidFunction(a_new_config_op).has_config_arg()

    config_param = DecoratedSolidFunction(a_new_config_op).get_config_arg()

    print(repr(config_param))


def test_new_config():
    class ANewConfigOpConfig(BaseModel):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_new_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction

    assert DecoratedSolidFunction(a_new_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_new_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE
    assert list(a_new_config_op.config_schema.config_type.fields.keys()) == ["a_string", "an_int"]

    @job
    def a_job():
        a_new_config_op()

    assert a_job

    from dagster._core.errors import DagsterInvalidConfigError

    with pytest.raises(DagsterInvalidConfigError):
        # ensure that config schema actually works
        a_job.execute_in_process(
            {"ops": {"a_new_config_op": {"config": {"a_string_mispelled": "foo", "an_int": 2}}}}
        )

    a_job.execute_in_process(
        {"ops": {"a_new_config_op": {"config": {"a_string": "foo", "an_int": 2}}}}
    )

    assert executed["yes"]


def test_nested_new_config():
    class ANestedConfig(BaseModel):
        a_string: str
        an_int: int

    class ANewConfigOpConfig(BaseModel):
        a_nested_value: ANestedConfig
        a_bool: bool

    executed = {}

    @op
    def a_new_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_nested_value.a_string == "foo"
        assert config.a_nested_value.an_int == 2
        assert config.a_bool == True

    from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction

    assert DecoratedSolidFunction(a_new_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_new_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE
    assert list(a_new_config_op.config_schema.config_type.fields.keys()) == [
        "a_nested_value",
        "a_bool",
    ]

    @job
    def a_job():
        a_new_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_new_config_op": {
                    "config": {"a_bool": True, "a_nested_value": {"a_string": "foo", "an_int": 2}}
                }
            }
        }
    )

    assert executed["yes"]


def test_new_config_permissive():
    class ANewConfigOpConfig(BaseModel, extra=Extra.allow):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_new_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction

    assert DecoratedSolidFunction(a_new_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_new_config_op.config_schema.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE
    assert list(a_new_config_op.config_schema.config_type.fields.keys()) == ["a_string", "an_int"]

    @job
    def a_job():
        a_new_config_op()

    assert a_job

    a_job.execute_in_process(
        {"ops": {"a_new_config_op": {"config": {"a_string": "foo", "an_int": 2, "a_bool": True}}}}
    )

    assert executed["yes"]


def test_new_config_descriptions_and_defaults():
    class ANewConfigOpConfig(BaseModel):
        """
        Config for my new op
        """

        a_string: str = Field(description="A string", default="bar")
        an_int: int = 5

    executed = {}

    @op
    def a_new_config_op(config: ANewConfigOpConfig):
        executed["yes"] = True
        assert config.a_string == "bar"
        assert config.an_int == 5

    from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction

    assert DecoratedSolidFunction(a_new_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_new_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE
    assert list(a_new_config_op.config_schema.config_type.fields.keys()) == ["a_string", "an_int"]
    assert a_new_config_op.config_schema.description == "Config for my new op"
    assert a_new_config_op.config_schema.config_type.fields["a_string"].description == "A string"
    assert a_new_config_op.config_schema.config_type.fields["a_string"].default_value == "bar"
    assert a_new_config_op.config_schema.config_type.fields["an_int"].default_value == 5

    @job
    def a_job():
        a_new_config_op()

    assert a_job

    a_job.execute_in_process({})

    assert executed["yes"]


# TODO: Union types
# Would be nice if we could use native Python unions
# e.g.
#
# class OpConfigOne(BaseModel):
#     a_string: str
#
# class OpConfigTwo(BaseModel):
#     an_int: int
#
# class OpConfig(BaseModel):
#     config: Union[OpConfigOne, OpConfigTwo]
#
# may be easer with https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions


def test_data_structures_new_config():
    class AListConfig(BaseModel):
        a_string_list: List[str]
        a_dict: Dict[str, int]
        another_dict: Mapping[str, bool]

    executed = {}

    @op
    def a_new_config_op(config: AListConfig):
        executed["yes"] = True
        assert config.a_string_list == ["foo", "bar"]
        assert config.a_dict == {"foo": 2}
        assert config.another_dict == {"foo": True}

    from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction

    assert DecoratedSolidFunction(a_new_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_new_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE
    assert list(a_new_config_op.config_schema.config_type.fields.keys()) == [
        "a_string_list",
        "a_dict",
        "another_dict",
    ]
    assert (
        a_new_config_op.config_schema.config_type.fields["a_string_list"].config_type.kind
        == ConfigTypeKind.ARRAY
    )
    assert (
        a_new_config_op.config_schema.config_type.fields["a_dict"].config_type.kind
        == ConfigTypeKind.MAP
    )
    assert (
        a_new_config_op.config_schema.config_type.fields["another_dict"].config_type.kind
        == ConfigTypeKind.MAP
    )

    @job
    def a_job():
        a_new_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_new_config_op": {
                    "config": {
                        "a_string_list": ["foo", "bar"],
                        "a_dict": {"foo": 2},
                        "another_dict": {"foo": True},
                    }
                }
            }
        }
    )

    assert executed["yes"]
