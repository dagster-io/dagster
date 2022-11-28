import pytest
from pydantic import BaseModel

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
