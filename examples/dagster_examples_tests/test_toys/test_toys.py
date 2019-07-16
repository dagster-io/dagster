import pytest

from dagster import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterTypeCheckError,
    RunConfig,
    execute_pipeline,
)

from dagster_examples.toys.config_mapping import config_mapping_pipeline
from dagster_examples.toys.error_monster import error_monster
from dagster_examples.toys.hammer import hammer_pipeline
from dagster_examples.toys.log_spew import log_spew
from dagster_examples.toys.many_events import many_events
from dagster_examples.toys.resources import resource_pipeline
from dagster_examples.toys.sleepy import sleepy_pipeline


def test_define_repo():
    from dagster_examples.toys.repo import define_repo

    assert define_repo()


def test_many_events_pipeline():
    assert execute_pipeline(many_events).success


def test_sleepy_pipeline():
    assert execute_pipeline(sleepy_pipeline).success


def test_hammer_pipeline():
    assert execute_pipeline(hammer_pipeline).success


def test_spew_pipeline():
    assert execute_pipeline(log_spew).success


def test_resource_pipeline_no_config():
    result = execute_pipeline(resource_pipeline)
    assert result.result_for_solid('one').output_value() == 2


def test_resource_pipeline_with_config():
    result = execute_pipeline(
        resource_pipeline, environment_dict={'resources': {'R1': {'config': 2}}}
    )
    assert result.result_for_solid('one').output_value() == 3


def test_error_monster_success():
    assert execute_pipeline(
        error_monster,
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
        error_monster,
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
            error_monster,
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
            error_monster,
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
    with pytest.raises(DagsterTypeCheckError):
        execute_pipeline(
            error_monster,
            environment_dict={
                'solids': {
                    'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': True}},
                    'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                },
                'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
            },
        )


def test_config_mapping():
    assert execute_pipeline(
        config_mapping_pipeline,
        environment_dict={
            'solids': {
                'outer_wrap': {
                    'config': {'outer_first': 'foo', 'outer_second': 'bar', 'outer_third': 3}
                }
            }
        },
    ).success
