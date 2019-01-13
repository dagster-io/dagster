import pytest

from dagster import (
    Any,
    Bool,
    Float,
    InputDefinition,
    Int,
    OutputDefinition,
    Path,
    PipelineDefinition,
    PipelineConfigEvaluationError,
    String,
    lambda_solid,
    execute_pipeline,
)

from dagster.utils.test import get_temp_file_name


def define_test_all_scalars_pipeline():
    @lambda_solid(inputs=[InputDefinition('num', Int)])
    def take_int(num):
        return num

    @lambda_solid(output=OutputDefinition(Int))
    def produce_int():
        return 2

    @lambda_solid(inputs=[InputDefinition('string', String)])
    def take_string(string):
        return string

    @lambda_solid(output=OutputDefinition(String))
    def produce_string():
        return 'foo'

    @lambda_solid(inputs=[InputDefinition('path', Path)])
    def take_path(path):
        return path

    @lambda_solid(output=OutputDefinition(Path))
    def produce_path():
        return '/path/to/foo'

    return PipelineDefinition(
        name='test_all_scalars_pipeline',
        solids=[take_int, produce_int, take_string, produce_string, take_path, produce_path],
    )


def single_input_env(solid_name, input_name, input_spec):
    return {'solids': {solid_name: {'inputs': {input_name: input_spec}}}}


def test_int_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_int', 'num', {'value': 2}),
        solid_subset=['take_int'],
    )

    assert result.success
    assert result.result_for_solid('take_int').transformed_value() == 2


def test_int_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_int', 'num', {'value': 'dkjdfkdj'}),
            solid_subset=['take_int'],
        )

    assert 'Type failure at path "root:solids:take_int:inputs:num:value" on type "Int"' in str(
        exc_info.value
    )


def single_output_env(solid_name, output_spec):
    return {'solids': {solid_name: {'outputs': [{'result': output_spec}]}}}


def test_int_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_int', {'json': {'path': tmp_file}}),
            solid_subset=['produce_int'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_int', 'num', {'json': {'path': tmp_file}}),
            solid_subset=['take_int'],
        )

        assert source_result.result_for_solid('take_int').transformed_value() == 2


def test_int_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_int', {'pickle': {'path': tmp_file}}),
            solid_subset=['produce_int'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_int', 'num', {'pickle': {'path': tmp_file}}),
            solid_subset=['take_int'],
        )

        assert source_result.result_for_solid('take_int').transformed_value() == 2


def test_string_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_string', 'string', {'value': 'dkjkfd'}),
        solid_subset=['take_string'],
    )

    assert result.success
    assert result.result_for_solid('take_string').transformed_value() == 'dkjkfd'


def test_string_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'value': 3343}),
            solid_subset=['take_string'],
        )

    assert (
        'Type failure at path "root:solids:take_string:inputs:string:value" on type "String"'
        in str(exc_info.value)
    )


def test_string_json_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_string', {'json': {'path': tmp_file}}),
            solid_subset=['produce_string'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'json': {'path': tmp_file}}),
            solid_subset=['take_string'],
        )

        assert source_result.result_for_solid('take_string').transformed_value() == 'foo'


def test_string_pickle_schema_roundtrip():
    with get_temp_file_name() as tmp_file:
        mat_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_output_env('produce_string', {'pickle': {'path': tmp_file}}),
            solid_subset=['produce_string'],
        )

        assert mat_result.success

        source_result = execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_string', 'string', {'pickle': {'path': tmp_file}}),
            solid_subset=['take_string'],
        )

        assert source_result.result_for_solid('take_string').transformed_value() == 'foo'


def test_path_input_schema_value():
    result = execute_pipeline(
        define_test_all_scalars_pipeline(),
        environment=single_input_env('take_path', 'path', '/a/path'),
        solid_subset=['take_path'],
    )

    assert result.success
    assert result.result_for_solid('take_path').transformed_value() == '/a/path'


def test_path_input_schema_failure():
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            define_test_all_scalars_pipeline(),
            environment=single_input_env('take_path', 'path', {'value': 3343}),
            solid_subset=['take_path'],
        )

    assert 'Type failure at path "root:solids:take_path:inputs:path" on type "String"' in str(
        exc_info.value
    )
