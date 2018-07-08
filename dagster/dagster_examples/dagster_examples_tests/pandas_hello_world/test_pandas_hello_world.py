import dagster
from dagster import config

from dagster.core.execution import execute_pipeline
from dagster.utils.test import script_relative_path

from dagster.dagster_examples.pandas_hello_world.pipeline import define_pipeline


def test_pipeline_include():
    assert define_pipeline()


def test_execute_pipeline():
    pipeline = define_pipeline()
    environment = config.Environment(
        inputs=[
            config.Input('num', {'path': script_relative_path('num.csv')}, source='CSV'),
        ],
    )

    result = execute_pipeline(
        dagster.context(),
        pipeline,
        environment=environment,
        from_solids=['sum_solid'],
        through_solids=[
            'sum_sq_solid',
        ]
    )

    assert result.success

    assert result.result_named('sum_solid').transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    assert result.result_named('sum_sq_solid').transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_sq': [9, 49],
    }
