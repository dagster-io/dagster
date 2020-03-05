import pytest

from dagster import (
    DagsterInvariantViolationError,
    ModeDefinition,
    execute_pipeline_with_mode,
    pipeline,
    resource,
    solid,
)


@resource
def add_one_resource(_):
    def add_one(num):
        return num + 1

    return add_one


@resource
def add_two_resource(_):
    def add_two(num):
        return num + 2

    return add_two


@solid(required_resource_keys={'adder'})
def solid_that_uses_adder_resource(context, number):
    return context.resources.adder(number)


@pipeline(
    mode_defs=[
        ModeDefinition(name='add_one', resource_defs={'adder': add_one_resource}),
        ModeDefinition(name='add_two', resource_defs={'adder': add_two_resource}),
    ]
)
def pipeline_with_mode():
    return solid_that_uses_adder_resource()


def test_execute_pipeline_with_mode():
    pipeline_result = execute_pipeline_with_mode(
        pipeline_with_mode,
        environment_dict={
            'solids': {'solid_that_uses_adder_resource': {'inputs': {'number': {'value': 4}}}}
        },
        mode='add_one',
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('solid_that_uses_adder_resource').output_value() == 5

    pipeline_result = execute_pipeline_with_mode(
        pipeline_with_mode,
        environment_dict={
            'solids': {'solid_that_uses_adder_resource': {'inputs': {'number': {'value': 4}}}}
        },
        mode='add_two',
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('solid_that_uses_adder_resource').output_value() == 6


def test_execute_pipeline_with_non_existant_mode():
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline_with_mode(
            pipeline_with_mode,
            'BAD',
            environment_dict={
                'solids': {'solid_that_uses_adder_resource': {'inputs': {'number': {'value': 4}}}}
            },
        )
