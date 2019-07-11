from dagster import execute_pipeline

from dagster_examples.intro_tutorial.reusing_solids import reusing_solids_pipeline


def test_run_whole_pipeline():
    pipeline_result = execute_pipeline(
        reusing_solids_pipeline,
        {
            'solids': {
                'a_plus_b': {'inputs': {'num1': {'value': 2}, 'num2': {'value': 6}}},
                'c_plus_d': {'inputs': {'num1': {'value': 4}, 'num2': {'value': 8}}},
            }
        },
    )

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('a_plus_b').output_value() == 8

    assert pipeline_result.result_for_solid('c_plus_d').output_value() == 12
    assert pipeline_result.result_for_solid('final').output_value() == 8 * 12
