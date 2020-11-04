import pytest
from dagster import (
    Any,
    Bool,
    DagsterInvalidConfigError,
    Float,
    InputDefinition,
    Int,
    List,
    Optional,
    OutputDefinition,
    PipelineDefinition,
    String,
    execute_pipeline,
    lambda_solid,
)
from dagster.utils.test import get_temp_file_name


def _execute_pipeline_with_subset(pipeline, run_config, solid_selection):
    return execute_pipeline(
        pipeline.get_pipeline_subset_def(solid_selection), run_config=run_config
    )


def define_test_all_scalars_pipeline():
    @lambda_solid(input_defs=[InputDefinition("num", Int)])
    def take_int(num):
        return num

    @lambda_solid(output_def=OutputDefinition(Int))
    def produce_int():
        return 2

    @lambda_solid(input_defs=[InputDefinition("string", String)])
    def take_string(string):
        return string

    @lambda_solid(output_def=OutputDefinition(String))
    def produce_string():
        return "foo"

    @lambda_solid(input_defs=[InputDefinition("float_number", Float)])
    def take_float(float_number):
        return float_number

    @lambda_solid(output_def=OutputDefinition(Float))
    def produce_float():
        return 3.14

    @lambda_solid(input_defs=[InputDefinition("bool_value", Bool)])
    def take_bool(bool_value):
        return bool_value

    @lambda_solid(output_def=OutputDefinition(Bool))
    def produce_bool():
        return True

    @lambda_solid(input_defs=[InputDefinition("any_value", Any)])
    def take_any(any_value):
        return any_value

    @lambda_solid(output_def=OutputDefinition(Any))
    def produce_any():
        return True

    @lambda_solid(input_defs=[InputDefinition("string_list", List[String])])
    def take_string_list(string_list):
        return string_list

    @lambda_solid(input_defs=[InputDefinition("nullable_string", Optional[String])])
    def take_nullable_string(nullable_string):
        return nullable_string

    return PipelineDefinition(
        name="test_all_scalars_pipeline",
        solid_defs=[
            produce_any,
            produce_bool,
            produce_float,
            produce_int,
            produce_string,
            take_any,
            take_bool,
            take_float,
            take_int,
            take_nullable_string,
            take_string,
            take_string_list,
        ],
    )


def single_input_env(solid_name, input_name, input_spec):
    return {"solids": {solid_name: {"inputs": {input_name: input_spec}}}}


def test_int_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config={"solids": {"take_int": {"inputs": {"num": {"value": 2}}}}},
        solid_selection={"take_int"},
    )

    assert result.success
    assert result.result_for_solid("take_int").output_value() == 2


def test_int_input_schema_raw_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config={"solids": {"take_int": {"inputs": {"num": 2}}}},
        solid_selection={"take_int"},
    )

    assert result.success
    assert result.result_for_solid("take_int").output_value() == 2


def test_int_input_schema_failure_wrong_value_type():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"value": "dkjdfkdj"}),
            solid_selection={"take_int"},
        )
    assert "Error 1: Invalid scalar at path root:solids:take_int:inputs:num:value" in str(
        exc_info.value
    )


def test_int_input_schema_failure_wrong_key():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"wrong_key": "dkjdfkdj"}),
            solid_selection={"take_int"},
        )
    assert (
        'Error 1: Received unexpected config entry "wrong_key" at path root:solids:take_int:inputs:num'
        in str(exc_info.value)
    )


def test_int_input_schema_failure_raw_string():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", "dkjdfkdj"),
            solid_selection={"take_int"},
        )
    assert "Error 1: Invalid scalar at path root:solids:take_int:inputs:num" in str(exc_info.value)


def single_output_env(solid_name, output_spec):
    return {"solids": {solid_name: {"outputs": [{"result": output_spec}]}}}


def test_int_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_int", {"json": {"path": tmp_file}}),
            solid_selection={"produce_int"},
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"json": {"path": tmp_file}}),
            solid_selection={"take_int"},
        )

        assert source_result.result_for_solid("take_int").output_value() == 2


def test_int_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_int", {"pickle": {"path": tmp_file}}),
            solid_selection={"produce_int"},
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"pickle": {"path": tmp_file}}),
            solid_selection={"take_int"},
        )

        assert source_result.result_for_solid("take_int").output_value() == 2


def test_string_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_string", "string", {"value": "dkjkfd"}),
        solid_selection={"take_string"},
    )

    assert result.success
    assert result.result_for_solid("take_string").output_value() == "dkjkfd"


def test_string_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"value": 3343}),
            solid_selection={"take_string"},
        )

    assert "Invalid scalar at path root:solids:take_string:inputs:string:value" in str(
        exc_info.value
    )


def test_float_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_float", "float_number", {"value": 3.34}),
        solid_selection={"take_float"},
    )

    assert result.success
    assert result.result_for_solid("take_float").output_value() == 3.34


def test_float_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_float", "float_number", {"value": "3343"}),
            solid_selection={"take_float"},
        )

    assert "Invalid scalar at path root:solids:take_float:inputs:float_number:value" in str(
        exc_info.value
    )


def test_bool_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_bool", "bool_value", {"value": True}),
        solid_selection={"take_bool"},
    )

    assert result.success
    assert result.result_for_solid("take_bool").output_value() is True


def test_bool_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_bool", "bool_value", {"value": "3343"}),
            solid_selection={"take_bool"},
        )

    assert "Invalid scalar at path root:solids:take_bool:inputs:bool_value:value" in str(
        exc_info.value
    )


def test_any_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_any", "any_value", {"value": "ff"}),
        solid_selection={"take_any"},
    )

    assert result.success
    assert result.result_for_solid("take_any").output_value() == "ff"

    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_any", "any_value", {"value": 3843}),
        solid_selection={"take_any"},
    )

    assert result.success
    assert result.result_for_solid("take_any").output_value() == 3843


def test_none_string_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", None),
            solid_selection={"take_string"},
        )

    assert len(exc_info.value.errors) == 1

    error = exc_info.value.errors[0]

    assert "Value at path root:solids:take_string:inputs:string must not be None." in error.message


def test_value_none_string_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"value": None}),
            solid_selection={"take_string"},
        )

    assert "Value at path root:solids:take_string:inputs:string:value must not be None" in str(
        exc_info.value
    )


def test_string_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_string", {"json": {"path": tmp_file}}),
            solid_selection={"produce_string"},
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"json": {"path": tmp_file}}),
            solid_selection={"take_string"},
        )

        assert source_result.result_for_solid("take_string").output_value() == "foo"


def test_string_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_string", {"pickle": {"path": tmp_file}}),
            solid_selection={"produce_string"},
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"pickle": {"path": tmp_file}}),
            solid_selection={"take_string"},
        )

        assert source_result.result_for_solid("take_string").output_value() == "foo"


def test_string_list_input():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_string_list", "string_list", [{"value": "foobar"}]),
        solid_selection={"take_string_list"},
    )

    assert result.success

    assert result.result_for_solid("take_string_list").output_value() == ["foobar"]


def test_nullable_string_input_with_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_nullable_string", "nullable_string", {"value": "foobar"}),
        solid_selection={"take_nullable_string"},
    )

    assert result.success

    assert result.result_for_solid("take_nullable_string").output_value() == "foobar"


def test_nullable_string_input_with_none_value():
    # Perhaps a confusing test case. Optional makes the entire enclosing structure nullable,
    # rather than the "value" value embedded within it
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_nullable_string", "nullable_string", {"value": None}),
            solid_selection={"take_nullable_string"},
        )

    assert (
        "Value at path root:solids:take_nullable_string:inputs:nullable_string:value must not be None"
    ) in str(exc_info.value)


def test_nullable_string_input_without_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_nullable_string", "nullable_string", None),
        solid_selection={"take_nullable_string"},
    )

    assert result.success

    assert result.result_for_solid("take_nullable_string").output_value() is None
