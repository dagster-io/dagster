import logging

import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    Dict,
    execute_pipeline,
    Field,
    logger,
    ModeDefinition,
    DagsterInvalidConfigError,
    PipelineDefinition,
    resource,
    RunConfig,
    solid,
    String,
)
from dagster.utils.test import execute_solids_within_pipeline
from dagster.core.definitions.environment_schema import create_environment_type
from dagster.core.log_manager import coerce_valid_log_level

from ..test_repository import (
    define_multi_mode_pipeline,
    define_multi_mode_with_resources_pipeline,
    define_single_mode_pipeline,
)


def test_default_mode_definition():
    pipeline_def = PipelineDefinition(name='takes a mode', solid_defs=[])
    assert pipeline_def


def test_mode_takes_a_name():
    pipeline_def = PipelineDefinition(
        name='takes a mode', solid_defs=[], mode_defs=[ModeDefinition(name='a_mode')]
    )
    assert pipeline_def


def test_execute_single_mode():
    single_mode_pipeline = define_single_mode_pipeline()
    assert single_mode_pipeline.is_single_mode is True

    assert execute_pipeline(single_mode_pipeline).result_for_solid('return_two').output_value() == 2

    assert (
        execute_pipeline(single_mode_pipeline, run_config=RunConfig(mode='the_mode'))
        .result_for_solid('return_two')
        .output_value()
        == 2
    )


def test_wrong_single_mode():
    with pytest.raises(DagsterInvariantViolationError):
        assert (
            execute_pipeline(define_single_mode_pipeline(), run_config=RunConfig(mode='wrong_mode'))
            .result_for_solid('return_two')
            .output_value()
            == 2
        )


def test_mode_double_default_name():
    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        PipelineDefinition(
            name='double_default', solid_defs=[], mode_defs=[ModeDefinition(), ModeDefinition()]
        )

    assert (
        str(ide.value) == 'Two modes seen with the name "default" in "double_default". '
        'Modes must have unique names.'
    )


def test_mode_double_given_name():
    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        PipelineDefinition(
            name='double_given',
            solid_defs=[],
            mode_defs=[ModeDefinition(name='given'), ModeDefinition(name='given')],
        )

    assert (
        str(ide.value) == 'Two modes seen with the name "given" in "double_given". '
        'Modes must have unique names.'
    )


def test_execute_multi_mode():
    multi_mode_pipeline = define_multi_mode_pipeline()

    assert (
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='mode_one'))
        .result_for_solid('return_three')
        .output_value()
        == 3
    )

    assert (
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='mode_two'))
        .result_for_solid('return_three')
        .output_value()
        == 3
    )


def test_execute_multi_mode_errors():
    multi_mode_pipeline = define_multi_mode_pipeline()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline)

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline, run_config=RunConfig(mode='wrong_mode'))


def test_execute_multi_mode_with_resources():
    pipeline_def = define_multi_mode_with_resources_pipeline()

    add_mode_result = execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='add_mode'),
        environment_dict={'resources': {'op': {'config': 2}}},
    )

    assert add_mode_result.result_for_solid('apply_to_three').output_value() == 5

    mult_mode_result = execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='mult_mode'),
        environment_dict={'resources': {'op': {'config': 3}}},
    )

    assert mult_mode_result.result_for_solid('apply_to_three').output_value() == 9


def test_correct_env_type_names_for_named():
    pipeline_def = define_multi_mode_with_resources_pipeline()

    mult_type_name = create_environment_type(pipeline_def, 'mult_mode')
    assert mult_type_name.key == 'MultiModeWithResources.Mode.MultMode.Environment'
    assert mult_type_name.name == 'MultiModeWithResources.Mode.MultMode.Environment'

    assert (
        mult_type_name.fields['resources'].config_type.key
        == 'MultiModeWithResources.Mode.MultMode.Resources'
    )
    assert (
        mult_type_name.fields['resources'].config_type.name
        == 'MultiModeWithResources.Mode.MultMode.Resources'
    )

    add_type_name = create_environment_type(pipeline_def, 'add_mode')

    assert add_type_name.key == 'MultiModeWithResources.Mode.AddMode.Environment'
    assert add_type_name.name == 'MultiModeWithResources.Mode.AddMode.Environment'

    assert (
        add_type_name.fields['resources'].config_type.key
        == 'MultiModeWithResources.Mode.AddMode.Resources'
    )
    assert (
        add_type_name.fields['resources'].config_type.name
        == 'MultiModeWithResources.Mode.AddMode.Resources'
    )


def test_mode_with_resource_deps():

    called = {'count': 0}

    @resource
    def resource_a(_init_context):
        return 1

    @solid(required_resource_keys={'a'})
    def requires_a(context):
        called['count'] += 1
        assert context.resources.a == 1

    pipeline_def_good_deps = PipelineDefinition(
        name='mode_with_good_deps',
        solid_defs=[requires_a],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a})],
    )

    execute_pipeline(pipeline_def_good_deps)

    assert called['count'] == 1

    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        PipelineDefinition(
            name='mode_with_bad_deps',
            solid_defs=[requires_a],
            mode_defs=[ModeDefinition(resource_defs={'ab': resource_a})],
        )

    assert (
        str(ide.value)
        == 'Resource "a" is required by solid requires_a, but is not provided by mode "default".'
    )

    @solid
    def no_deps(context):
        called['count'] += 1
        assert context.resources.a == 1

    pipeline_def_no_deps = PipelineDefinition(
        name='mode_with_no_deps',
        solid_defs=[no_deps],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a})],
    )

    execute_pipeline(pipeline_def_no_deps)

    assert called['count'] == 2


def test_subset_with_mode_definitions():

    called = {'a': 0, 'b': 0}

    @resource
    def resource_a(_init_context):
        return 1

    @solid(required_resource_keys={'a'})
    def requires_a(context):
        called['a'] += 1
        assert context.resources.a == 1

    @resource
    def resource_b(_init_context):
        return 2

    @solid(required_resource_keys={'b'})
    def requires_b(context):
        called['b'] += 1
        assert context.resources.b == 2

    pipeline_def = PipelineDefinition(
        name='subset_test',
        solid_defs=[requires_a, requires_b],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})],
    )

    assert execute_pipeline(pipeline_def).success is True

    assert called == {'a': 1, 'b': 1}

    assert (
        execute_solids_within_pipeline(pipeline_def, solid_names=['requires_a'])[
            'requires_a'
        ].success
        is True
    )

    assert called == {'a': 2, 'b': 1}


def define_multi_mode_with_loggers_pipeline():
    foo_logger_captured_results = []
    bar_logger_captured_results = []

    @logger(
        config_field=Field(
            Dict({'log_level': Field(String, is_optional=True, default_value='INFO')})
        )
    )
    def foo_logger(init_context):
        logger_ = logging.Logger('foo')
        logger_.log = lambda level, msg, **kwargs: foo_logger_captured_results.append((level, msg))
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config['log_level']))
        return logger_

    @logger(
        config_field=Field(
            Dict({'log_level': Field(String, is_optional=True, default_value='INFO')})
        )
    )
    def bar_logger(init_context):
        logger_ = logging.Logger('bar')
        logger_.log = lambda level, msg, **kwargs: bar_logger_captured_results.append((level, msg))
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config['log_level']))
        return logger_

    @solid
    def return_six(context):
        context.log.critical('Here we are')
        return 6

    return (
        PipelineDefinition(
            name='multi_mode',
            solid_defs=[return_six],
            mode_defs=[
                ModeDefinition(name='foo_mode', logger_defs={'foo': foo_logger}),
                ModeDefinition(
                    name='foo_bar_mode', logger_defs={'foo': foo_logger, 'bar': bar_logger}
                ),
            ],
        ),
        foo_logger_captured_results,
        bar_logger_captured_results,
    )


def parse_captured_results(captured_results):
    parsed_captured_results = [
        [y.strip().split(' = ') for y in x[1].strip().split('\n')] for x in captured_results
    ]
    # the captured results are a list of lists of two-member lists [log_msg_key, log_msg_value]
    # this double list comprehension grabs the log_msg_value where log_msg_key == 'orig_message'
    original_messages = [
        item[1]
        for result in parsed_captured_results
        for item in result
        if item[0] == 'orig_message'
    ]
    return original_messages


def test_execute_multi_mode_loggers_with_single_logger():
    pipeline_def, foo_logger_captured_results, bar_logger_captured_results = (
        define_multi_mode_with_loggers_pipeline()
    )

    execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='foo_mode'),
        environment_dict={'loggers': {'foo': {'config': {'log_level': 'DEBUG'}}}},
    )

    assert not bar_logger_captured_results

    original_messages = parse_captured_results(foo_logger_captured_results)

    assert len(list(filter(lambda x: x == '"Here we are"', original_messages))) == 1


def test_execute_multi_mode_loggers_with_single_logger_extra_config():
    pipeline_def, _, __ = define_multi_mode_with_loggers_pipeline()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline_def,
            run_config=RunConfig(mode='foo_mode'),
            environment_dict={
                'loggers': {
                    'foo': {'config': {'log_level': 'DEBUG'}},
                    'bar': {'config': {'log_level': 'DEBUG'}},
                }
            },
        )


def test_execute_multi_mode_loggers_with_multiple_loggers():
    pipeline_def, foo_logger_captured_results, bar_logger_captured_results = (
        define_multi_mode_with_loggers_pipeline()
    )

    execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='foo_bar_mode'),
        environment_dict={
            'loggers': {
                'foo': {'config': {'log_level': 'DEBUG'}},
                'bar': {'config': {'log_level': 'DEBUG'}},
            }
        },
    )

    foo_original_messages = parse_captured_results(foo_logger_captured_results)

    assert len(list(filter(lambda x: x == '"Here we are"', foo_original_messages))) == 1

    bar_original_messages = parse_captured_results(bar_logger_captured_results)

    assert len(list(filter(lambda x: x == '"Here we are"', bar_original_messages))) == 1


def test_execute_multi_mode_loggers_with_multiple_loggers_single_config():
    pipeline_def, foo_logger_captured_results, bar_logger_captured_results = (
        define_multi_mode_with_loggers_pipeline()
    )

    execute_pipeline(
        pipeline_def,
        run_config=RunConfig(mode='foo_bar_mode'),
        environment_dict={'loggers': {'foo': {'config': {'log_level': 'DEBUG'}}}},
    )

    foo_original_messages = parse_captured_results(foo_logger_captured_results)

    assert len(list(filter(lambda x: x == '"Here we are"', foo_original_messages))) == 1

    assert not bar_logger_captured_results
