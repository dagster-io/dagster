import sys

import pytest

from dagster import execute_pipeline, RunConfig

from dagstermill import DagstermillError
from dagstermill.examples.repository import (
    define_add_pipeline,
    define_error_pipeline,
    define_hello_world_pipeline,
    define_hello_world_with_output_pipeline,
    define_test_notebook_dag_pipeline,
    define_tutorial_pipeline,
    define_no_repo_registration_error_pipeline,
)


# Notebooks encode what version of python (e.g. their kernel)
# they run on, so we can't run notebooks in python2 atm
def notebook_test(f):
    return pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
        All of the development notebooks currently use the python3 "kernel" so they will
        not be executable in a container that only have python2.7 (e.g. in CircleCI)
        ''',
    )(f)


@notebook_test
def test_hello_world():
    result = execute_pipeline(define_hello_world_pipeline())
    assert result.success


@notebook_test
def test_hello_world_with_output():
    pipeline = define_hello_world_with_output_pipeline()
    result = execute_pipeline(pipeline)
    assert result.success
    assert result.result_for_solid('hello_world_output').transformed_value() == 'hello, world'


@notebook_test
def test_add_pipeline():
    pipeline = define_add_pipeline()
    result = execute_pipeline(
        pipeline, {'context': {'default': {'config': {'log_level': 'ERROR'}}}}
    )
    assert result.success
    assert result.result_for_solid('add_two_numbers').transformed_value() == 3


@notebook_test
def test_notebook_dag():
    pipeline_result = execute_pipeline(
        define_test_notebook_dag_pipeline(),
        environment_dict={'solids': {'load_a': {'config': 1}, 'load_b': {'config': 2}}},
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_two').transformed_value() == 3
    assert pipeline_result.result_for_solid('mult_two').transformed_value() == 6


@notebook_test
def test_error_notebook():
    with pytest.raises(DagstermillError, match='Someone set up us the bomb'):
        execute_pipeline(define_error_pipeline())
    res = execute_pipeline(define_error_pipeline(), run_config=RunConfig.nonthrowing_in_process())
    assert not res.success
    assert res.step_event_list[0].event_type.value == 'STEP_FAILURE'


@notebook_test
def test_tutorial_pipeline():
    pipeline = define_tutorial_pipeline()
    result = execute_pipeline(
        pipeline, {'context': {'default': {'config': {'log_level': 'DEBUG'}}}}
    )
    assert result.success


@notebook_test
def test_no_repo_registration_error():
    with pytest.raises(
        DagstermillError,
        match='If Dagstermill solids have outputs that require serialization strategies',
    ):
        execute_pipeline(define_no_repo_registration_error_pipeline())
    res = execute_pipeline(define_no_repo_registration_error_pipeline(), throw_on_user_error=False)
    assert not res.success
