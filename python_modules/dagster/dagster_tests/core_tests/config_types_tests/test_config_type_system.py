import re
import string
import typing

import pytest
from dagster import (
    Any,
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    Field,
    Float,
    Int,
    List,
    ModeDefinition,
    Noneable,
    Permissive,
    PipelineDefinition,
    ResourceDefinition,
    Set,
    String,
    Tuple,
    composite_solid,
    execute_pipeline,
    execute_solid,
    pipeline,
    solid,
)
from dagster.config.errors import DagsterEvaluationErrorReason
from dagster.config.field_utils import convert_potential_field
from dagster.config.validate import process_config, validate_config


def test_noop_config():
    assert Field(Any)


def test_int_field():
    config_field = convert_potential_field({"int_field": Int})
    assert validate_config(config_field.config_type, {"int_field": 1}).value == {"int_field": 1}


def test_float_field():
    config_field = convert_potential_field({"float_field": Float})
    assert validate_config(config_field.config_type, {"float_field": 1.0}).value == {
        "float_field": 1.0
    }
    assert process_config(config_field.config_type, {"float_field": 1.0}).value == {
        "float_field": 1.0
    }
    assert validate_config(config_field.config_type, {"float_field": 1}).value == {"float_field": 1}
    assert process_config(config_field.config_type, {"float_field": 1}).value == {
        "float_field": 1.0
    }


def assert_config_value_success(config_type, config_value, expected):
    result = process_config(config_type, config_value)
    assert result.success
    assert result.value == expected


def assert_eval_failure(config_type, value):
    assert not validate_config(config_type, value).success


def test_int_fails():
    config_field = convert_potential_field({"int_field": Int})

    assert_eval_failure(config_field.config_type, {"int_field": "fjkdj"})
    assert_eval_failure(config_field.config_type, {"int_field": True})


def test_default_arg():
    config_field = convert_potential_field(
        {"int_field": Field(Int, default_value=2, is_required=False)}
    )

    assert_config_value_success(config_field.config_type, {}, {"int_field": 2})


def test_default_float_arg():
    config_field = convert_potential_field(
        {"float_field": Field(Float, default_value=2.0, is_required=False)}
    )

    assert_config_value_success(config_field.config_type, {}, {"float_field": 2.0})

    config_field = convert_potential_field(
        {"float_field": Field(Float, default_value=2, is_required=False)}
    )

    assert_config_value_success(config_field.config_type, {}, {"float_field": 2})


def _single_required_string_config_dict():
    return convert_potential_field({"string_field": String})


def _multiple_required_fields_config_dict():
    return convert_potential_field({"field_one": String, "field_two": String})


def _single_optional_string_config_dict():
    return convert_potential_field({"optional_field": Field(String, is_required=False)})


def _single_optional_string_field_config_dict_with_default():
    optional_field_def = Field(String, is_required=False, default_value="some_default")
    return convert_potential_field({"optional_field": optional_field_def})


def _mixed_required_optional_string_config_dict_with_default():
    return convert_potential_field(
        {
            "optional_arg": Field(String, is_required=False, default_value="some_default"),
            "required_arg": Field(String, is_required=True),
            "optional_arg_no_default": Field(String, is_required=False),
        }
    )


def _multiple_required_fields_config_permissive_dict():
    return Field(Permissive({"field_one": Field(String), "field_two": Field(String)}))


def _validate(config_field, value):
    res = process_config(config_field.config_type, value)
    assert res.success, res.errors[0].message
    return res.value


def test_single_required_string_field_config_type():
    assert _validate(_single_required_string_config_dict(), {"string_field": "value"}) == {
        "string_field": "value"
    }

    with pytest.raises(
        AssertionError,
        match='Missing required config entry "string_field" at the root.',
    ):
        _validate(_single_required_string_config_dict(), {})

    with pytest.raises(AssertionError):
        _validate(_single_required_string_config_dict(), {"extra": "yup"})

    with pytest.raises(AssertionError):
        _validate(_single_required_string_config_dict(), {"string_field": "yupup", "extra": "yup"})

    with pytest.raises(AssertionError):
        _validate(_single_required_string_config_dict(), {"string_field": 1})


def test_undefined_field_error():
    with pytest.raises(
        AssertionError,
        match=(
            'Received unexpected config entry "extra" at the root. Expected: "{ string_field: '
            'String }".'
        ),
    ):
        _validate(
            _single_required_string_config_dict(), {"string_field": "value", "extra": "extra"}
        )


def test_multiple_required_fields_passing():
    assert (
        _validate(
            _multiple_required_fields_config_dict(),
            {"field_one": "value_one", "field_two": "value_two"},
        )
        == {"field_one": "value_one", "field_two": "value_two"}
    )


def test_multiple_required_fields_failing():
    with pytest.raises(AssertionError):
        _validate(_multiple_required_fields_config_dict(), {})

    with pytest.raises(AssertionError):
        _validate(_multiple_required_fields_config_dict(), {"field_one": "yup"})

    with pytest.raises(AssertionError):
        _validate(_multiple_required_fields_config_dict(), {"field_one": "yup", "extra": "yup"})

    with pytest.raises(AssertionError):
        _validate(
            _multiple_required_fields_config_dict(),
            {"field_one": "yup", "field_two": "yup", "extra": "should_not_exist"},
        )

    with pytest.raises(AssertionError):
        _validate(
            _multiple_required_fields_config_dict(), {"field_one": "value_one", "field_two": 2}
        )


def test_single_optional_field_passing():
    assert _validate(_single_optional_string_config_dict(), {"optional_field": "value"}) == {
        "optional_field": "value"
    }
    assert _validate(_single_optional_string_config_dict(), {}) == {}

    with pytest.raises(AssertionError):
        assert _validate(_single_optional_string_config_dict(), {"optional_field": None}) == {
            "optional_field": None
        }


def test_single_optional_field_failing():
    with pytest.raises(AssertionError):

        _validate(_single_optional_string_config_dict(), {"optional_field": 1})

    with pytest.raises(AssertionError):
        _validate(_single_optional_string_config_dict(), {"dlkjfalksdjflksaj": 1})


def test_single_optional_field_passing_with_default():
    assert _validate(_single_optional_string_field_config_dict_with_default(), {}) == {
        "optional_field": "some_default"
    }

    assert _validate(
        _single_optional_string_field_config_dict_with_default(), {"optional_field": "override"}
    ) == {"optional_field": "override"}


def test_permissive_multiple_required_fields_passing():
    assert _validate(
        _multiple_required_fields_config_permissive_dict(),
        {
            "field_one": "value_one",
            "field_two": "value_two",
            "previously_unspecified": "should_exist",
        },
    ) == {
        "field_one": "value_one",
        "field_two": "value_two",
        "previously_unspecified": "should_exist",
    }


def test_permissive_multiple_required_fields_nested_passing():
    assert _validate(
        _multiple_required_fields_config_permissive_dict(),
        {
            "field_one": "value_one",
            "field_two": "value_two",
            "previously_unspecified": {"nested": "value", "with_int": 2},
        },
    ) == {
        "field_one": "value_one",
        "field_two": "value_two",
        "previously_unspecified": {"nested": "value", "with_int": 2},
    }


def test_permissive_multiple_required_fields_failing():
    with pytest.raises(AssertionError):
        _validate(_multiple_required_fields_config_permissive_dict(), {})

    with pytest.raises(AssertionError):
        _validate(_multiple_required_fields_config_permissive_dict(), {"field_one": "yup"})

    with pytest.raises(AssertionError):
        _validate(
            _multiple_required_fields_config_permissive_dict(),
            {"field_one": "value_one", "field_two": 2},
        )


def test_mixed_args_passing():
    assert (
        _validate(
            _mixed_required_optional_string_config_dict_with_default(),
            {"optional_arg": "value_one", "required_arg": "value_two"},
        )
        == {"optional_arg": "value_one", "required_arg": "value_two"}
    )

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {"required_arg": "value_two"}
    ) == {"optional_arg": "some_default", "required_arg": "value_two"}

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(),
        {"required_arg": "value_two", "optional_arg_no_default": "value_three"},
    ) == {
        "optional_arg": "some_default",
        "required_arg": "value_two",
        "optional_arg_no_default": "value_three",
    }


def _single_nested_config():
    return convert_potential_field({"nested": {"int_field": Int}})


def _nested_optional_config_with_default():
    return convert_potential_field(
        {"nested": {"int_field": Field(Int, is_required=False, default_value=3)}}
    )


def _nested_optional_config_with_no_default():
    return convert_potential_field({"nested": {"int_field": Field(Int, is_required=False)}})


def test_single_nested_config():
    assert _validate(_single_nested_config(), {"nested": {"int_field": 2}}) == {
        "nested": {"int_field": 2}
    }


def test_single_nested_config_undefined_errors():
    with pytest.raises(
        AssertionError,
        match='Value at path root:nested must be dict. Expected: "{ int_field: Int }".',
    ):
        _validate(_single_nested_config(), {"nested": "dkjfdk"})

    with pytest.raises(
        AssertionError,
        match='Invalid scalar at path root:nested:int_field. Value "dkjfdk" of type .* is not valid for expected type "Int".',
    ):
        _validate(_single_nested_config(), {"nested": {"int_field": "dkjfdk"}})

    with pytest.raises(
        AssertionError,
        match=(
            'Received unexpected config entry "not_a_field" at path root:nested. Expected: '
            '"{ int_field: Int }".'
        ),
    ):
        _validate(_single_nested_config(), {"nested": {"int_field": 2, "not_a_field": 1}})

    with pytest.raises(
        AssertionError,
        match="Invalid scalar at path root:nested:int_field. Value \"{'too_nested': 'dkjfdk'}\" of type .* is not valid for expected type \"Int\".",
    ):
        _validate(_single_nested_config(), {"nested": {"int_field": {"too_nested": "dkjfdk"}}})


def test_nested_optional_with_default():
    assert _validate(_nested_optional_config_with_default(), {"nested": {"int_field": 2}}) == {
        "nested": {"int_field": 2}
    }

    assert _validate(_nested_optional_config_with_default(), {"nested": {}}) == {
        "nested": {"int_field": 3}
    }


def test_nested_optional_with_no_default():
    assert _validate(_nested_optional_config_with_no_default(), {"nested": {"int_field": 2}}) == {
        "nested": {"int_field": 2}
    }

    assert _validate(_nested_optional_config_with_no_default(), {"nested": {}}) == {"nested": {}}


def test_config_defaults():
    @solid(config_schema={"sum": Int})
    def two(_context):
        assert _context.solid_config["sum"] == 6
        return _context.solid_config["sum"]

    @solid(config_schema={"sum": Int})
    def one(_context, prev_sum):
        assert prev_sum == 6
        return prev_sum + _context.solid_config["sum"]

    # addition_composite_solid
    def addition_composite_solid_config_fn(config):
        child_config = {"config": {"sum": config["a"] + config["b"] + config["c"]}}
        return {"one": child_config, "two": child_config}

    @composite_solid(
        config_fn=addition_composite_solid_config_fn,
        config_schema={
            "a": Field(Int, is_required=False, default_value=1),
            "b": Field(Int, is_required=False, default_value=2),
            "c": Int,
        },
    )
    def addition_composite_solid():
        return one(two())

    @pipeline
    def addition_pipeline():
        addition_composite_solid()

    result = execute_pipeline(
        addition_pipeline, {"solids": {"addition_composite_solid": {"config": {"c": 3}}}}
    )

    assert result.success


def test_config_with_and_without_config():
    @solid(config_schema={"prefix": Field(str, is_required=False, default_value="_")})
    def prefix_value(context, v):
        return "{prefix}{v}".format(prefix=context.solid_config["prefix"], v=v)

    @composite_solid(
        config_fn=lambda cfg: {"prefix_value": {"config": {"prefix": cfg["prefix"]}}},
        config_schema={"prefix": Field(str, is_required=False, default_value="_id_")},
    )
    def prefix_id(val):
        return prefix_value(val)

    @solid
    def print_value(_, v):
        return str(v)

    @pipeline
    def config_issue_pipeline():
        v = prefix_id()
        print_value(v)

    result = execute_pipeline(
        config_issue_pipeline,
        {
            "solids": {
                "prefix_id": {
                    "config": {"prefix": "_customprefix_"},
                    "inputs": {"val": {"value": "12345"}},
                }
            }
        },
    )

    assert result.success
    assert result.result_for_solid("print_value").output_value() == "_customprefix_12345"

    result_using_default = execute_pipeline(
        config_issue_pipeline,
        {"solids": {"prefix_id": {"config": {}, "inputs": {"val": {"value": "12345"}}}}},
    )

    assert result_using_default.success
    assert result_using_default.result_for_solid("print_value").output_value() == "_id_12345"


def test_build_optionality():
    optional_test_type = convert_potential_field(
        {
            "required": {"value": String},
            "optional": {"value": Field(String, is_required=False)},
        }
    ).config_type

    assert optional_test_type.fields["required"].is_required
    assert optional_test_type.fields["optional"].is_required is False


def test_wrong_solid_name():
    @solid(name="some_solid", input_defs=[], output_defs=[], config_schema=Int)
    def some_solid(_):
        return None

    @pipeline(name="pipeline_wrong_solid_name")
    def pipeline_def():
        some_solid()

    env_config = {"solids": {"another_name": {"config": {}}}}

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(pipeline_def, env_config)

    pe = pe_info.value

    assert 'Received unexpected config entry "another_name" at path root:solids' in str(pe)


def fail_me():
    assert False


def dummy_resource(config_schema=None):
    return ResourceDefinition(lambda _: None, config_schema=config_schema)


def test_wrong_resources():
    pipeline_def = PipelineDefinition(
        name="pipeline_test_multiple_context",
        mode_defs=[
            ModeDefinition(
                resource_defs={"resource_one": dummy_resource(), "resource_two": dummy_resource()}
            )
        ],
        solid_defs=[],
    )

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Received unexpected config entry "nope" at path root:resources',
    ):
        execute_pipeline(pipeline_def, {"resources": {"nope": {}}})


def test_solid_list_config():
    value = [1, 2]
    called = {}

    @solid(name="solid_list_config", input_defs=[], output_defs=[], config_schema=[int])
    def solid_list_config(context):
        assert context.solid_config == value
        called["yup"] = True

    @pipeline(name="solid_list_config_pipeline")
    def pipeline_def():
        solid_list_config()

    result = execute_pipeline(
        pipeline_def, run_config={"solids": {"solid_list_config": {"config": value}}}
    )

    assert result.success
    assert called["yup"]


def test_two_list_types():
    @solid(
        input_defs=[],
        config_schema={"list_one": [int], "list_two": [int]},
    )
    def two_list_type(context):
        return context.solid_config

    assert (
        execute_solid(
            two_list_type,
            run_config={
                "solids": {"two_list_type": {"config": {"list_one": [1], "list_two": [2]}}}
            },
        ).output_value()
        == {"list_one": [1], "list_two": [2]}
    )

    @solid(
        input_defs=[],
        config_schema={"list_one": [Int], "list_two": [Int]},
    )
    def two_list_type_condensed_syntax(context):
        return context.solid_config

    assert (
        execute_solid(
            two_list_type_condensed_syntax,
            run_config={
                "solids": {
                    "two_list_type_condensed_syntax": {"config": {"list_one": [1], "list_two": [2]}}
                }
            },
        ).output_value()
        == {"list_one": [1], "list_two": [2]}
    )

    @solid(
        input_defs=[],
        config_schema={"list_one": [int], "list_two": [int]},
    )
    def two_list_type_condensed_syntax_primitives(context):
        return context.solid_config

    assert (
        execute_solid(
            two_list_type_condensed_syntax_primitives,
            run_config={
                "solids": {
                    "two_list_type_condensed_syntax_primitives": {
                        "config": {"list_one": [1], "list_two": [2]}
                    }
                }
            },
        ).output_value()
        == {"list_one": [1], "list_two": [2]}
    )


def test_multilevel_default_handling():
    @solid(config_schema=Field(Int, is_required=False, default_value=234))
    def has_default_value(context):
        assert context.solid_config == 234

    pipeline_def = PipelineDefinition(
        name="multilevel_default_handling", solid_defs=[has_default_value]
    )

    assert execute_pipeline(pipeline_def).success
    assert execute_pipeline(pipeline_def, run_config=None).success
    assert execute_pipeline(pipeline_def, run_config={}).success
    assert execute_pipeline(pipeline_def, run_config={"solids": {}}).success
    assert execute_pipeline(pipeline_def, run_config={"solids": {"has_default_value": {}}}).success

    assert execute_pipeline(
        pipeline_def, run_config={"solids": {"has_default_value": {"config": 234}}}
    ).success


def test_no_env_missing_required_error_handling():
    @solid(config_schema=Int)
    def required_int_solid(_context):
        pass

    pipeline_def = PipelineDefinition(
        name="no_env_missing_required_error", solid_defs=[required_int_solid]
    )

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(pipeline_def)

    assert isinstance(pe_info.value, DagsterInvalidConfigError)
    pe = pe_info.value
    assert len(pe.errors) == 1
    mfe = pe.errors[0]
    assert mfe.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert len(pe.errors) == 1

    expected_suggested_config = {"solids": {"required_int_solid": {"config": 0}}}
    assert pe.errors[0].message.startswith('Missing required config entry "solids" at the root.')
    assert str(expected_suggested_config) in pe.errors[0].message


def test_root_extra_field():
    @solid(config_schema=Int)
    def required_int_solid(_context):
        pass

    @pipeline
    def pipeline_def():
        required_int_solid()

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(
            pipeline_def,
            run_config={"solids": {"required_int_solid": {"config": 948594}}, "nope": None},
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    fnd = pe.errors[0]
    assert fnd.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert 'Received unexpected config entry "nope"' in pe.message


def test_deeper_path():
    @solid(config_schema=Int)
    def required_int_solid(_context):
        pass

    @pipeline
    def pipeline_def():
        required_int_solid()

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(
            pipeline_def, run_config={"solids": {"required_int_solid": {"config": "asdf"}}}
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    rtm = pe.errors[0]
    assert rtm.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_working_list_path():
    called = {}

    @solid(config_schema=[int])
    def required_list_int_solid(context):
        assert context.solid_config == [1, 2]
        called["yup"] = True

    @pipeline
    def pipeline_def():
        required_list_int_solid()

    result = execute_pipeline(
        pipeline_def, run_config={"solids": {"required_list_int_solid": {"config": [1, 2]}}}
    )

    assert result.success
    assert called["yup"]


def test_item_error_list_path():
    called = {}

    @solid(config_schema=[int])
    def required_list_int_solid(context):
        assert context.solid_config == [1, 2]
        called["yup"] = True

    @pipeline
    def pipeline_def():
        required_list_int_solid()

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(
            pipeline_def,
            run_config={"solids": {"required_list_int_solid": {"config": [1, "nope"]}}},
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    rtm = pe.errors[0]
    assert rtm.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH

    assert "Invalid scalar at path root:solids:required_list_int_solid:config[1]" in str(pe)


def test_list_in_config_error():
    error_msg = (
        "Cannot use List in the context of config. "
        "Please use a python list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead."
    )

    with pytest.raises(DagsterInvalidDefinitionError, match=re.escape(error_msg)):

        @solid(config_schema=List[int])
        def _no_runtime_list_in_config(_):
            pass


def test_required_resource_not_given():
    @solid(required_resource_keys={"required"})
    def needs_resource(_):
        pass

    @pipeline(
        name="required_resource_not_given",
        mode_defs=[ModeDefinition(resource_defs={"required": dummy_resource(Int)})],
    )
    def pipeline_def():
        needs_resource()

    with pytest.raises(DagsterInvalidConfigError) as not_none_pe_info:
        execute_pipeline(pipeline_def, run_config={"resources": None})

    assert len(not_none_pe_info.value.errors) == 1
    assert (
        "Value at path root:resources must not be None." in not_none_pe_info.value.errors[0].message
    )

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(pipeline_def, run_config={"resources": {}})

    pe = pe_info.value
    error = pe.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD

    expected_suggested_config = {"required": {"config": 0}}
    assert error.message.startswith(
        'Missing required config entry "required" at path root:resources.'
    )
    assert str(expected_suggested_config) in error.message


def test_multilevel_good_error_handling_solids():
    @solid(config_schema=Int)
    def good_error_handling(_context):
        pass

    @pipeline
    def pipeline_def():
        good_error_handling()

    with pytest.raises(DagsterInvalidConfigError) as not_none_pe_info:
        execute_pipeline(pipeline_def, run_config={"solids": None})

    assert len(not_none_pe_info.value.errors) == 1
    assert "Value at path root:solids must not be None." in not_none_pe_info.value.errors[0].message

    with pytest.raises(DagsterInvalidConfigError) as missing_field_pe_info:
        execute_pipeline(pipeline_def, run_config={"solids": {}})

    assert len(missing_field_pe_info.value.errors) == 1

    expected_suggested_config = {"good_error_handling": {"config": 0}}
    assert missing_field_pe_info.value.errors[0].message.startswith(
        """Missing required config entry "good_error_handling" at path root:solids."""
    )
    assert str(expected_suggested_config) in missing_field_pe_info.value.errors[0].message


def test_multilevel_good_error_handling_solid_name_solids():
    @solid(config_schema=Int)
    def good_error_handling(_context):
        pass

    @pipeline
    def pipeline_def():
        good_error_handling()

    with pytest.raises(DagsterInvalidConfigError) as pe_info:
        execute_pipeline(pipeline_def, run_config={"solids": {"good_error_handling": {}}})

    assert len(pe_info.value.errors) == 1

    expected_suggested_config = {"config": 0}
    assert pe_info.value.errors[0].message.startswith(
        """Missing required config entry "config" at path root:solids:good_error_handling."""
    )
    assert str(expected_suggested_config) in pe_info.value.errors[0].message


def test_multilevel_good_error_handling_config_solids_name_solids():
    @solid(config_schema=Noneable(int))
    def good_error_handling(_context):
        pass

    @pipeline
    def pipeline_def():
        good_error_handling()

    execute_pipeline(pipeline_def, run_config={"solids": {"good_error_handling": {"config": None}}})


def test_invalid_default_values():
    with pytest.raises(
        DagsterInvalidConfigError,
        match='Value "3" of type .* is not valid for expected type "Int"',
    ):

        @solid(config_schema=Field(Int, default_value="3"))
        def _solid(_):
            pass


def test_typing_types_into_config():
    match_str = re.escape(
        "You have passed in typing.List to the config system. "
        "Types from the typing module in python are not allowed "
        "in the config system. You must use types that are imported "
        "from dagster or primitive types such as bool, int, etc."
    )
    with pytest.raises(DagsterInvalidDefinitionError, match=match_str):

        @solid(config_schema=Field(typing.List))
        def _solid(_):
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match=match_str):

        @solid(config_schema=typing.List)
        def _solid(_):
            pass

    match_str = re.escape(
        "You have passed in typing.List[int] to the config system. Types "
        "from the typing module in python are not allowed in the config system. "
        "You must use types that are imported from dagster or primitive types "
        "such as bool, int, etc."
    )

    with pytest.raises(DagsterInvalidDefinitionError, match=match_str):

        @solid(config_schema=Field(typing.List[int]))
        def _solid(_):
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match=match_str):

        @solid(config_schema=typing.List[int])
        def _solid(_):
            pass

    for ttype in [
        typing.Optional[int],
        typing.Set,
        typing.Set[int],
        typing.Dict,
        typing.Dict[int, str],
        typing.Tuple,
        typing.Tuple[int, int],
    ]:
        with pytest.raises(DagsterInvalidDefinitionError):

            @solid(config_schema=Field(ttype))
            def _solid(_):
                pass


def test_no_set_in_config_system():
    set_error_msg = re.escape("Cannot use Set in the context of a config field.")
    with pytest.raises(DagsterInvalidDefinitionError, match=set_error_msg):

        @solid(config_schema=Field(Set))
        def _bare_open_set(_):
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match=set_error_msg):

        @solid(config_schema=Set)
        def _bare_open_set(_):
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match=set_error_msg):

        @solid(config_schema=Field(Set[int]))
        def _bare_closed_set(_):
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match=set_error_msg):

        @solid(config_schema=Set[int])
        def _bare_closed_set(_):
            pass


def test_no_tuple_in_config_system():
    tuple_error_msg = re.escape("Cannot use Tuple in the context of a config field.")
    with pytest.raises(DagsterInvalidDefinitionError, match=tuple_error_msg):

        @solid(config_schema=Field(Tuple))
        def _bare_open_tuple(_):
            pass

    with pytest.raises(DagsterInvalidDefinitionError, match=tuple_error_msg):

        @solid(config_schema=Field(Tuple[int]))
        def _bare_closed_set(_):
            pass


def test_field_is_none():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema={"none_field": None})
        def _none_is_bad(_):
            pass

    assert "Fields cannot be None" in str(exc_info.value)


def test_permissive_defaults():
    @solid(config_schema=Permissive({"four": Field(int, default_value=4)}))
    def perm_with_defaults(context):
        assert context.solid_config["four"] == 4

    assert execute_solid(perm_with_defaults).success


def test_permissive_ordering():
    alphabet = {letter: letter for letter in string.ascii_lowercase}

    @solid(config_schema=dict)
    def test_order(context):
        alpha = list(context.solid_config.keys())
        for idx, letter in enumerate(string.ascii_lowercase):
            assert letter == alpha[idx]  # if this fails dict ordering got messed up

    assert execute_solid(
        test_order, run_config={"solids": {"test_order": {"config": alphabet}}}
    ).success
