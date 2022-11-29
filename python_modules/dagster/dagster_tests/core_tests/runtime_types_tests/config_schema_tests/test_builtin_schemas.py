import pytest

from dagster import (
    Any,
    Bool,
    DagsterInvalidConfigError,
    Float,
    GraphDefinition,
    In,
    Int,
    List,
    Optional,
    Out,
    String,
    op,
)
from dagster._utils.test import get_temp_file_name


def _execute_pipeline_with_subset(pipeline, run_config, op_selection):
    return pipeline.get_job_def_for_subset_selection(op_selection).execute_in_process(
        run_config=run_config
    )


def define_test_all_scalars_pipeline():
    @op(ins={"num": In(Int)})
    def take_int(num):
        return num

    @op(out=Out(Int))
    def produce_int():
        return 2

    @op(ins={"string": In(String)})
    def take_string(string):
        return string

    @op(out=Out(String))
    def produce_string():
        return "foo"

    @op(ins={"float_number": In(Float)})
    def take_float(float_number):
        return float_number

    @op(out=Out(Float))
    def produce_float():
        return 3.14

    @op(ins={"bool_value": In(Bool)})
    def take_bool(bool_value):
        return bool_value

    @op(out=Out(Bool))
    def produce_bool():
        return True

    @op(ins={"any_value": In(Any)})
    def take_any(any_value):
        return any_value

    @op(out=Out(Any))
    def produce_any():
        return True

    @op(ins={"string_list": In(List[String])})
    def take_string_list(string_list):
        return string_list

    @op(ins={"nullable_string": In(Optional[String])})
    def take_nullable_string(nullable_string):
        return nullable_string

    return GraphDefinition(
        name="test_all_scalars_pipeline",
        node_defs=[
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
    ).to_job()


def single_input_env(solid_name, input_name, input_spec):
    return {"ops": {solid_name: {"inputs": {input_name: input_spec}}}}


def test_int_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config={"ops": {"take_int": {"inputs": {"num": {"value": 2}}}}},
        op_selection=["take_int"],
    )

    assert result.success
    assert result.output_for_node("take_int") == 2


def test_int_input_schema_raw_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config={"ops": {"take_int": {"inputs": {"num": 2}}}},
        op_selection=["take_int"],
    )

    assert result.success
    assert result.output_for_node("take_int") == 2


def test_int_input_schema_failure_wrong_value_type():
    with pytest.raises(
        DagsterInvalidConfigError, match="Invalid scalar at path root:ops:take_int:inputs:num:value"
    ):
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"value": "dkjdfkdj"}),
            op_selection=["take_int"],
        )


def test_int_input_schema_failure_wrong_key():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"wrong_key": "dkjdfkdj"}),
            op_selection=["take_int"],
        )
    assert (
        'Error 1: Received unexpected config entry "wrong_key" at path root:ops:take_int:inputs:num'
        in str(exc_info.value)
    )


def test_int_input_schema_failure_raw_string():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", "dkjdfkdj"),
            op_selection=["take_int"],
        )
    assert "Error 1: Invalid scalar at path root:ops:take_int:inputs:num" in str(exc_info.value)


def single_output_env(solid_name, output_spec):
    return {"ops": {solid_name: {"outputs": [{"result": output_spec}]}}}


def test_int_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_int", {"json": {"path": tmp_file}}),
            op_selection=["produce_int"],
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"json": {"path": tmp_file}}),
            op_selection=["take_int"],
        )

        assert source_result.output_for_node("take_int") == 2


def test_int_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_int", {"pickle": {"path": tmp_file}}),
            op_selection=["produce_int"],
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_int", "num", {"pickle": {"path": tmp_file}}),
            op_selection=["take_int"],
        )

        assert source_result.output_for_node("take_int") == 2


def test_string_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_string", "string", {"value": "dkjkfd"}),
        op_selection=["take_string"],
    )

    assert result.success
    assert result.output_for_node("take_string") == "dkjkfd"


def test_string_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"value": 3343}),
            op_selection=["take_string"],
        )

    assert "Invalid scalar at path root:ops:take_string:inputs:string:value" in str(exc_info.value)


def test_float_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_float", "float_number", {"value": 3.34}),
        op_selection=["take_float"],
    )

    assert result.success
    assert result.output_for_node("take_float") == 3.34


def test_float_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_float", "float_number", {"value": "3343"}),
            op_selection=["take_float"],
        )

    assert "Invalid scalar at path root:ops:take_float:inputs:float_number:value" in str(
        exc_info.value
    )


def test_bool_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_bool", "bool_value", {"value": True}),
        op_selection=["take_bool"],
    )

    assert result.success
    assert result.output_for_node("take_bool") is True


def test_bool_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_bool", "bool_value", {"value": "3343"}),
            op_selection=["take_bool"],
        )

    assert "Invalid scalar at path root:ops:take_bool:inputs:bool_value:value" in str(
        exc_info.value
    )


def test_any_input_schema_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_any", "any_value", {"value": "ff"}),
        op_selection=["take_any"],
    )

    assert result.success
    assert result.output_for_node("take_any") == "ff"

    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_any", "any_value", {"value": 3843}),
        op_selection=["take_any"],
    )

    assert result.success
    assert result.output_for_node("take_any") == 3843


def test_none_string_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", None),
            op_selection=["take_string"],
        )

    assert len(exc_info.value.errors) == 1

    error = exc_info.value.errors[0]

    assert "Value at path root:ops:take_string:inputs:string must not be None." in error.message


def test_value_none_string_input_schema_failure():
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"value": None}),
            op_selection=["take_string"],
        )

    assert "Value at path root:ops:take_string:inputs:string:value must not be None" in str(
        exc_info.value
    )


def test_string_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_string", {"json": {"path": tmp_file}}),
            op_selection=["produce_string"],
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"json": {"path": tmp_file}}),
            op_selection=["take_string"],
        )

        assert source_result.output_for_node("take_string") == "foo"


def test_string_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_output_env("produce_string", {"pickle": {"path": tmp_file}}),
            op_selection=["produce_string"],
        )

        assert mat_result.success

        source_result = _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_string", "string", {"pickle": {"path": tmp_file}}),
            op_selection=["take_string"],
        )

        assert source_result.output_for_node("take_string") == "foo"


def test_string_list_input():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_string_list", "string_list", [{"value": "foobar"}]),
        op_selection=["take_string_list"],
    )

    assert result.success

    assert result.output_for_node("take_string_list") == ["foobar"]


def test_nullable_string_input_with_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_nullable_string", "nullable_string", {"value": "foobar"}),
        op_selection=["take_nullable_string"],
    )

    assert result.success

    assert result.output_for_node("take_nullable_string") == "foobar"


def test_nullable_string_input_with_none_value():
    # Perhaps a confusing test case. Optional makes the entire enclosing structure nullable,
    # rather than the "value" value embedded within it
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        _execute_pipeline_with_subset(
            define_test_all_scalars_pipeline(),
            run_config=single_input_env("take_nullable_string", "nullable_string", {"value": None}),
            op_selection=["take_nullable_string"],
        )

    assert (
        "Value at path root:ops:take_nullable_string:inputs:nullable_string:value must not be None"
    ) in str(exc_info.value)


def test_nullable_string_input_without_value():
    result = _execute_pipeline_with_subset(
        define_test_all_scalars_pipeline(),
        run_config=single_input_env("take_nullable_string", "nullable_string", None),
        op_selection=["take_nullable_string"],
    )

    assert result.success

    assert result.output_for_node("take_nullable_string") is None
