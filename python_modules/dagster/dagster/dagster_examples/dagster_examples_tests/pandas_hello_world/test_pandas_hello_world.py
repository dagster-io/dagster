import os

from dagster import config
from dagster.core.execution import execute_pipeline
from dagster.utils.test import script_relative_path
from dagster.cli.pipeline import (
    do_execute_command,
    print_pipeline,
    print_solids,
)

from dagster.dagster_examples.pandas_hello_world.pipeline import define_pipeline


def test_pipeline_include():
    assert define_pipeline()


def test_execute_pipeline():
    pipeline = define_pipeline()
    environment = config.Environment(
        sources={
            'sum_solid': {
                'num': config.Source(name='CSV', args={'path': script_relative_path('num.csv')})
            }
        },
        execution=config.Execution(from_solids=['sum_solid'], through_solids=['sum_sq_solid']),
    )

    result = execute_pipeline(pipeline, environment=environment)

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


def test_cli_execute():

    # currently paths in env files have to be relative to where the
    # script has launched so we have to simulate that
    cwd = os.getcwd()
    try:

        os.chdir(script_relative_path('../..'))

        do_execute_command(
            define_pipeline(),
            script_relative_path('../../pandas_hello_world/env.yml'),
            lambda *_args, **_kwargs: None,
        )
    finally:
        # restore cwd
        os.chdir(cwd)


def test_cli_print():
    print_pipeline(define_pipeline(), full=False, print_fn=lambda *_args, **_kwargs: None)
    print_pipeline(define_pipeline(), full=True, print_fn=lambda *_args, **_kwargs: None)
    print_solids(define_pipeline(), print_fn=lambda *_args, **_kwargs: None)
