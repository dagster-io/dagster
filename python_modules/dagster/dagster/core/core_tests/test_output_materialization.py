from dagster import (
    PipelineDefinition,
    OutputDefinition,
    execute_pipeline,
    lambda_solid,
    types,
)

from dagster.utils.test import get_temp_file_name

from dagster.core.config_types import (
    solid_has_config_entry,
    solid_has_materializable_outputs,
    is_materializeable,
)


def test_solid_has_config_entry():
    pipeline = single_int_output_pipeline()
    assert is_materializeable(types.Int)
    assert solid_has_materializable_outputs(pipeline.solid_named('return_one').definition)
    assert solid_has_config_entry(pipeline.solid_named('return_one').definition)


import json


def test_basic_json_materialization():
    return
    pipeline = single_int_output_pipeline()

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            pipeline,
            {
                'solids': {
                    'return_one': {
                        'outputs': {
                            'result': {
                                'json': {
                                    'path': filename,
                                },
                            },
                        },
                    }
                },
            },
        )

        assert result.success

        with open(filename, 'r+b') as ff:
            value = json.loads(ff.read())
            assert value == 1


def single_int_output_pipeline():
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_one():
        return 1

    return PipelineDefinition(name='basic_materialization_pipeline', solids=[return_one])
