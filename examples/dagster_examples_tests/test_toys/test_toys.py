import pytest
from dagster_examples.toys.composition import composition
from dagster_examples.toys.config_mapping import config_mapping_pipeline
from dagster_examples.toys.error_monster import error_monster
from dagster_examples.toys.hammer import hammer_pipeline
from dagster_examples.toys.log_spew import log_spew
from dagster_examples.toys.many_events import many_events
from dagster_examples.toys.resources import resource_pipeline
from dagster_examples.toys.resources_error import resource_error_pipeline
from dagster_examples.toys.sleepy import sleepy_pipeline

from dagster import (
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterTypeCheckDidNotPass,
    execute_pipeline,
)


def test_define_repo():
    from dagster_examples.toys.repo import toys_repository

    assert toys_repository


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
    result = execute_pipeline(resource_pipeline, run_config={'resources': {'R1': {'config': 2}}})
    assert result.result_for_solid('one').output_value() == 3


def test_error_monster_success():
    assert execute_pipeline(
        error_monster,
        run_config={
            'solids': {
                'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
            },
            'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
        },
    ).success

    assert execute_pipeline(
        pipeline=error_monster,
        mode='errorable_mode',
        run_config={
            'solids': {
                'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
            },
            'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
        },
    ).success


def test_error_monster_wrong_mode():
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(
            pipeline=error_monster,
            mode='nope',
            run_config={
                'solids': {
                    'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                },
                'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
            },
        )


def test_error_monster_success_error_on_resource():
    with pytest.raises(DagsterResourceFunctionError):
        execute_pipeline(
            error_monster,
            run_config={
                'solids': {
                    'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                    'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                },
                'resources': {'errorable_resource': {'config': {'throw_on_resource_init': True}}},
            },
        )


def test_error_monster_type_error():
    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(
            error_monster,
            run_config={
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
        run_config={
            'solids': {
                'outer_wrap': {
                    'config': {'outer_first': 'foo', 'outer_second': 'bar', 'outer_third': 3}
                }
            }
        },
    ).success


def test_error_resource(snapshot):
    result = execute_pipeline(
        resource_error_pipeline, run_config={'storage': {'filesystem': {}}}, raise_on_error=False,
    )

    assert not result.success
    assert len(result.event_list) >= 1

    init_failure_event = result.event_list[-1]
    assert init_failure_event.event_type_value == 'PIPELINE_INIT_FAILURE'
    snapshot.assert_match(init_failure_event.message)


def test_composition_pipeline():
    result = execute_pipeline(
        composition, run_config={'solids': {'add_four': {'inputs': {'num': 3}}}},
    )

    assert result.success

    assert result.output_for_solid('div_four') == 7.0 / 4.0
