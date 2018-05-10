from dagster_examples.qhp.pipeline import define_pipeline
from solidic.execution import (
    execute_solid_in_pipeline, SolidExecutionContext, execute_pipeline_and_collect
)
from solidic_utils.test import script_relative_path


def providers_771_args():
    return {
        'qhp_json_input': {
            'path': script_relative_path('providers-771.json'),
        }
    }


def test_plans():
    pipeline = define_pipeline()

    result = execute_solid_in_pipeline(
        SolidExecutionContext(),
        pipeline,
        input_arg_dicts=providers_771_args(),
        output_name='plans',
    )

    plans_df = result.materialized_output

    assert not plans_df.empty


def test_plan_years():
    pipeline = define_pipeline()

    result = execute_solid_in_pipeline(
        SolidExecutionContext(),
        pipeline,
        input_arg_dicts=providers_771_args(),
        output_name='plan_years',
    )

    plan_years_df = result.materialized_output

    assert not plan_years_df.empty


def test_plan_and_plan_years_pipeline():
    pipeline = define_pipeline()

    results = execute_pipeline_and_collect(
        SolidExecutionContext(), pipeline, providers_771_args(), ['plans', 'plan_years']
    )
    assert len(results) == 2


def test_insurance_pipeline():
    pipeline = define_pipeline()

    result = execute_solid_in_pipeline(
        SolidExecutionContext(),
        pipeline,
        providers_771_args(),
        output_name='insurance',
    )
    if result.exception:
        raise result.exception
    assert result.success
    assert result.name == 'insurance'
    assert not result.materialized_output.empty