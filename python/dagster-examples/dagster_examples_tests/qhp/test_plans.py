from dagster_examples.qhp.pipeline import define_pipeline
from solidic.execution import (execute_solid_in_pipeline, SolidExecutionContext)
from solidic_utils.test import script_relative_path


def test_create_pipeline():
    pipeline = define_pipeline()
    assert pipeline

    input_arg_dicts = {
        'qhp_json_input': {
            'path': script_relative_path('providers-771.json'),
        }
    }

    result = execute_solid_in_pipeline(
        SolidExecutionContext(),
        pipeline,
        input_arg_dicts=input_arg_dicts,
        output_name='plans',
    )

    plans_df = result.materialized_output

    assert not plans_df.empty
