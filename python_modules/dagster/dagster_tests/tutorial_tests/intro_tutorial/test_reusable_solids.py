from dagster import execute_pipeline

from dagster.tutorials.intro_tutorial.reusable_solids import define_reusable_solids_pipeline


def test_run_whole_pipeline():
    pipeline = define_reusable_solids_pipeline()
    pipeline_result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'a_plus_b': {'inputs': {'num1': {'value': 2}, 'num2': {'value': 6}}},
                'c_plus_d': {'inputs': {'num1': {'value': 4}, 'num2': {'value': 8}}},
            }
        },
    )

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('a_plus_b').transformed_value() == 8

    assert pipeline_result.result_for_solid('c_plus_d').transformed_value() == 12
    assert pipeline_result.result_for_solid('final').transformed_value() == 8 * 12
