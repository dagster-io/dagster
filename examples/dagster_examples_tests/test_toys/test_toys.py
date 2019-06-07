import pytest

from dagster import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    RunConfig,
    execute_pipeline,
)
from dagster_examples.toys.many_events import define_many_events_pipeline
from dagster_examples.toys.resources import define_resource_pipeline
from dagster_examples.toys.error_monster import define_error_monster_pipeline
from dagster_examples.toys.sleepy import define_sleepy_pipeline
from dagster_examples.toys.hammer import define_hammer_pipeline
from dagster_examples.toys.log_spew import define_spew_pipeline


def test_define_repo():
    from dagster_examples.toys.repo import define_repo

    assert define_repo()


def test_many_events_pipeline():
    assert execute_pipeline(define_many_events_pipeline()).success


def test_sleepy_pipeline():
    assert execute_pipeline(define_sleepy_pipeline()).success


def test_hammer_pipeline():
    assert execute_pipeline(define_hammer_pipeline()).success


def test_spew_pipeline():
    assert execute_pipeline(define_spew_pipeline()).success


def test_resource_pipeline_no_config():
    result = execute_pipeline(define_resource_pipeline())
    assert result.result_for_solid('one').result_value() == 2


def test_resource_pipeline_with_config():
    result = execute_pipeline(
        define_resource_pipeline(), environment_dict={'resources': {'R1': {'config': 2}}}
    )
    assert result.result_for_solid('one').result_value() == 3


def test_error_monster_success():
    assert execute_pipeline(
        define_error_monster_pipeline(),
        environment_dict={
            'solids': {
                'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
            },
            'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
        },
    ).success

    assert execute_pipeline(
        define_error_monster_pipeline(),
        environment_dict={
            'solids': {
                'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
            },
            'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
        },
        run_config=RunConfig(mode='errorable_mode'),
    ).success


def test_error_monster_wrong_mode():
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            define_error_monster_pipeline(),
            environment_dict={
                'solids': {
                    'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                },
                'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
            },
            run_config=RunConfig(mode='nope'),
        )


def test_error_monster_success_error_on_resource():
    with pytest.raises(DagsterResourceFunctionError):
        execute_pipeline(
            define_error_monster_pipeline(),
            environment_dict={
                'solids': {
                    'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                },
                'resources': {'errorable_resource': {'config': {'throw_on_resource_init': True}}},
            },
        )


def test_error_monster_type_error():
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            define_error_monster_pipeline(),
            environment_dict={
                'solids': {
                    'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': True}},
                    'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                },
                'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
            },
        )
