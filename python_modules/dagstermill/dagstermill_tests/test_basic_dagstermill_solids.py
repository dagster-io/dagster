import pytest

from dagster import execute_pipeline, RunConfig

from dagstermill import DagstermillError
from dagstermill.test_utils import notebook_test
from dagstermill.examples.repository import (
    define_add_pipeline,
    define_error_pipeline,
    define_hello_world_pipeline,
    define_hello_world_explicit_yield_pipeline,
    define_hello_world_with_output_pipeline,
    define_test_notebook_dag_pipeline,
    define_tutorial_pipeline,
    define_no_repo_registration_error_pipeline,
)


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
def test_hello_world_explicit_yield():
    result = execute_pipeline(define_hello_world_explicit_yield_pipeline())
    materializations = [
        x for x in result.event_list if x.event_type_value == 'STEP_MATERIALIZATION'
    ]
    assert len(materializations) == 2
    assert materializations[0].event_specific_data.materialization.path.startswith(
        '/tmp/dagstermill/'
    )
    assert materializations[1].event_specific_data.materialization.path == '/path/to/file'


@notebook_test
def test_add_pipeline():
    pipeline = define_add_pipeline()
    result = execute_pipeline(
        pipeline, {'loggers': {'console': {'config': {'log_level': 'ERROR'}}}}
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
    with pytest.raises(
        DagstermillError, match='Error occurred during the execution of Dagstermill solid'
    ) as exc:
        execute_pipeline(define_error_pipeline())
    assert 'Someone set up us the bomb' in exc.value.original_exc_info[1].args[0]
    res = execute_pipeline(define_error_pipeline(), run_config=RunConfig.nonthrowing_in_process())
    assert not res.success
    assert res.step_event_list[1].event_type.value == 'STEP_FAILURE'


@notebook_test
def test_tutorial_pipeline():
    pipeline = define_tutorial_pipeline()
    result = execute_pipeline(
        pipeline, {'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}}
    )
    assert result.success


@notebook_test
def test_no_repo_registration_error():
    with pytest.raises(
        DagstermillError,
        match='Error occurred during the execution of Dagstermill solid no_repo_reg',
    ) as exc:
        execute_pipeline(define_no_repo_registration_error_pipeline())
    assert (
        'If Dagstermill solids have outputs that require serialization strategies'
        in exc.value.original_exc_info[1].args[0]
    )
    res = execute_pipeline(
        define_no_repo_registration_error_pipeline(), run_config=RunConfig.nonthrowing_in_process()
    )
    assert not res.success
