import pytest

from dagster import (
    PipelineDefinition,
    ModeDefinition,
    execute_pipeline,
    RunConfig,
    Field,
    Int,
    solid,
    resource,
    DagsterInvariantViolationError,
)


def test_basic_mode_definition():
    pipeline_def = PipelineDefinition(
        name='takes a mode', solids=[], mode_definitions=[ModeDefinition()]
    )
    assert pipeline_def


def test_mode_takes_a_name():
    pipeline_def = PipelineDefinition(
        name='takes a mode', solids=[], mode_definitions=[ModeDefinition(name='a_mode')]
    )
    assert pipeline_def


def define_modeless_pipeline():
    @solid
    def return_one(_context):
        return 1

    return PipelineDefinition(name='modeless', solids=[return_one])


def define_single_mode_pipeline():
    @solid
    def return_two(_context):
        return 2

    return PipelineDefinition(
        name='single_mode', solids=[return_two], mode_definitions=[ModeDefinition(name='the_mode')]
    )


def define_multi_mode_pipeline():
    @solid
    def return_three(_context):
        return 3

    return PipelineDefinition(
        name='multi_mode',
        solids=[return_three],
        mode_definitions=[ModeDefinition(name='mode_one'), ModeDefinition('mode_two')],
    )


def test_execute_modeless():
    pipeline_result = execute_pipeline(define_modeless_pipeline())
    assert pipeline_result.result_for_solid('return_one').transformed_value() == 1


def test_execute_single_mode():
    single_mode_pipeline = define_single_mode_pipeline()
    assert single_mode_pipeline.is_modeless is False
    assert single_mode_pipeline.is_single_mode is True

    assert (
        execute_pipeline(single_mode_pipeline).result_for_solid('return_two').transformed_value()
        == 2
    )

    assert (
        execute_pipeline(single_mode_pipeline, run_config=RunConfig(mode='the_mode'))
        .result_for_solid('return_two')
        .transformed_value()
        == 2
    )


def test_wrong_single_mode():
    with pytest.raises(DagsterInvariantViolationError):
        assert (
            execute_pipeline(define_single_mode_pipeline(), run_config=RunConfig(mode='wrong_mode'))
            .result_for_solid('return_two')
            .transformed_value()
            == 2
        )


def test_execute_multi_mode():
    multi_mode_pipeline = define_multi_mode_pipeline()

    assert (
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='mode_one'))
        .result_for_solid('return_three')
        .transformed_value()
        == 3
    )

    assert (
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='mode_two'))
        .result_for_solid('return_three')
        .transformed_value()
        == 3
    )


def test_execute_multi_mode_errors():
    multi_mode_pipeline = define_multi_mode_pipeline()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline)

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='wrong_mode'))


def define_multi_mode_with_resources_pipeline():
    @resource(config_field=Field(Int))
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_field=Field(Int))
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @solid
    def apply_to_three(context):
        return context.resources.op(3)

    return PipelineDefinition(
        name='multi_mode',
        solids=[apply_to_three],
        mode_definitions=[
            ModeDefinition(name='add_mode', resources={'op': adder_resource}),
            ModeDefinition(name='mult_mode', resources={'op': multer_resource}),
        ],
    )


def test_execute_multi_mode_with_resources():
    pipeline_def = define_multi_mode_with_resources_pipeline()

    add_mode_result = execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='add_mode'),
        environment_dict={'resources': {'op': {'config': 2}}},
    )

    assert add_mode_result.result_for_solid('apply_to_three').transformed_value() == 5

    mult_mode_result = execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='mult_mode'),
        environment_dict={'resources': {'op': {'config': 3}}},
    )

    assert mult_mode_result.result_for_solid('apply_to_three').transformed_value() == 9
