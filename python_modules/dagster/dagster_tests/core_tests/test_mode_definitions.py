import logging

import pytest
from dagster import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    Field,
    ModeDefinition,
    PipelineDefinition,
    String,
    execute_pipeline,
    logger,
    pipeline,
    resource,
    solid,
)
from dagster.core.log_manager import coerce_valid_log_level
from dagster.utils.test import execute_solids_within_pipeline
from dagster_tests.general_tests.test_repository import (
    define_multi_mode_pipeline,
    define_multi_mode_with_resources_pipeline,
    define_single_mode_pipeline,
)


def test_default_mode_definition():
    pipeline_def = PipelineDefinition(name="takesamode", solid_defs=[])
    assert pipeline_def


def test_mode_takes_a_name():
    pipeline_def = PipelineDefinition(
        name="takesamode", solid_defs=[], mode_defs=[ModeDefinition(name="a_mode")]
    )
    assert pipeline_def


def test_mode_from_resources():
    @solid(required_resource_keys={"three"})
    def ret_three(context):
        return context.resources.three

    @pipeline(
        name="takesamode", mode_defs=[ModeDefinition.from_resources({"three": 3}, name="three")]
    )
    def pipeline_def():
        ret_three()

    assert execute_pipeline(pipeline_def).result_for_solid("ret_three").output_value() == 3


def test_execute_single_mode():
    single_mode_pipeline = define_single_mode_pipeline()
    assert single_mode_pipeline.is_single_mode is True

    assert execute_pipeline(single_mode_pipeline).result_for_solid("return_two").output_value() == 2

    assert (
        execute_pipeline(single_mode_pipeline, mode="the_mode")
        .result_for_solid("return_two")
        .output_value()
        == 2
    )


def test_wrong_single_mode():
    with pytest.raises(DagsterInvariantViolationError):
        assert (
            execute_pipeline(pipeline=define_single_mode_pipeline(), mode="wrong_mode")
            .result_for_solid("return_two")
            .output_value()
            == 2
        )


def test_mode_double_default_name():
    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        PipelineDefinition(
            name="double_default", solid_defs=[], mode_defs=[ModeDefinition(), ModeDefinition()]
        )

    assert (
        str(ide.value) == 'Two modes seen with the name "default" in "double_default". '
        "Modes must have unique names."
    )


def test_mode_double_given_name():
    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        PipelineDefinition(
            name="double_given",
            solid_defs=[],
            mode_defs=[ModeDefinition(name="given"), ModeDefinition(name="given")],
        )

    assert (
        str(ide.value) == 'Two modes seen with the name "given" in "double_given". '
        "Modes must have unique names."
    )


def test_execute_multi_mode():
    multi_mode_pipeline = define_multi_mode_pipeline()

    assert (
        execute_pipeline(pipeline=multi_mode_pipeline, mode="mode_one")
        .result_for_solid("return_three")
        .output_value()
        == 3
    )

    assert (
        execute_pipeline(pipeline=multi_mode_pipeline, mode="mode_two")
        .result_for_solid("return_three")
        .output_value()
        == 3
    )


def test_execute_multi_mode_errors():
    multi_mode_pipeline = define_multi_mode_pipeline()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(multi_mode_pipeline)

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipeline=multi_mode_pipeline, mode="wrong_mode")


def test_execute_multi_mode_with_resources():
    pipeline_def = define_multi_mode_with_resources_pipeline()

    add_mode_result = execute_pipeline(
        pipeline=pipeline_def,
        mode="add_mode",
        run_config={"resources": {"op": {"config": 2}}},
    )

    assert add_mode_result.result_for_solid("apply_to_three").output_value() == 5

    mult_mode_result = execute_pipeline(
        pipeline=pipeline_def,
        mode="mult_mode",
        run_config={"resources": {"op": {"config": 3}}},
    )

    assert mult_mode_result.result_for_solid("apply_to_three").output_value() == 9


def test_mode_with_resource_deps():

    called = {"count": 0}

    @resource
    def resource_a(_init_context):
        return 1

    @solid(required_resource_keys={"a"})
    def requires_a(context):
        called["count"] += 1
        assert context.resources.a == 1

    pipeline_def_good_deps = PipelineDefinition(
        name="mode_with_good_deps",
        solid_defs=[requires_a],
        mode_defs=[ModeDefinition(resource_defs={"a": resource_a})],
    )

    execute_pipeline(pipeline_def_good_deps)

    assert called["count"] == 1

    with pytest.raises(DagsterInvalidDefinitionError) as ide:
        PipelineDefinition(
            name="mode_with_bad_deps",
            solid_defs=[requires_a],
            mode_defs=[ModeDefinition(resource_defs={"ab": resource_a})],
        )

    assert (
        str(ide.value)
        == 'Resource "a" is required by solid def requires_a, but is not provided by mode "default".'
    )

    @solid(required_resource_keys={"a"})
    def no_deps(context):
        called["count"] += 1
        assert context.resources.a == 1

    pipeline_def_no_deps = PipelineDefinition(
        name="mode_with_no_deps",
        solid_defs=[no_deps],
        mode_defs=[ModeDefinition(resource_defs={"a": resource_a})],
    )

    execute_pipeline(pipeline_def_no_deps)

    assert called["count"] == 2


def test_subset_with_mode_definitions():

    called = {"a": 0, "b": 0}

    @resource
    def resource_a(_init_context):
        return 1

    @solid(required_resource_keys={"a"})
    def requires_a(context):
        called["a"] += 1
        assert context.resources.a == 1

    @resource
    def resource_b(_init_context):
        return 2

    @solid(required_resource_keys={"b"})
    def requires_b(context):
        called["b"] += 1
        assert context.resources.b == 2

    pipeline_def = PipelineDefinition(
        name="subset_test",
        solid_defs=[requires_a, requires_b],
        mode_defs=[ModeDefinition(resource_defs={"a": resource_a, "b": resource_b})],
    )

    assert execute_pipeline(pipeline_def).success is True

    assert called == {"a": 1, "b": 1}

    assert (
        execute_solids_within_pipeline(pipeline_def, solid_names={"requires_a"})[
            "requires_a"
        ].success
        is True
    )

    assert called == {"a": 2, "b": 1}


def define_multi_mode_with_loggers_pipeline():
    foo_logger_captured_results = []
    bar_logger_captured_results = []

    @logger(config_schema={"log_level": Field(String, is_required=False, default_value="INFO")})
    def foo_logger(init_context):
        logger_ = logging.Logger("foo")
        logger_.log = lambda level, msg, **kwargs: foo_logger_captured_results.append((level, msg))
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config["log_level"]))
        return logger_

    @logger(config_schema={"log_level": Field(String, is_required=False, default_value="INFO")})
    def bar_logger(init_context):
        logger_ = logging.Logger("bar")
        logger_.log = lambda level, msg, **kwargs: bar_logger_captured_results.append((level, msg))
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config["log_level"]))
        return logger_

    @solid
    def return_six(context):
        context.log.critical("Here we are")
        return 6

    return (
        PipelineDefinition(
            name="multi_mode",
            solid_defs=[return_six],
            mode_defs=[
                ModeDefinition(name="foo_mode", logger_defs={"foo": foo_logger}),
                ModeDefinition(
                    name="foo_bar_mode", logger_defs={"foo": foo_logger, "bar": bar_logger}
                ),
            ],
        ),
        foo_logger_captured_results,
        bar_logger_captured_results,
    )


def parse_captured_results(captured_results):
    # each result will be a tuple like:
    # (10,
    # 'multi_mode - 1cc8958b-5ce6-401a-9e2a-ddd653e59a7e - PIPELINE_START - Started execution of '
    # 'pipeline "multi_mode".'
    # )
    # so, this will reconstruct the original message from the captured log line.

    # Extract the text string and remove key = value tuples on later lines
    return [x[1].split("\n")[0] for x in captured_results]


def test_execute_multi_mode_loggers_with_single_logger():
    (
        pipeline_def,
        foo_logger_captured_results,
        bar_logger_captured_results,
    ) = define_multi_mode_with_loggers_pipeline()

    execute_pipeline(
        pipeline=pipeline_def,
        mode="foo_mode",
        run_config={"loggers": {"foo": {"config": {"log_level": "DEBUG"}}}},
    )

    assert not bar_logger_captured_results

    original_messages = parse_captured_results(foo_logger_captured_results)
    assert len([x for x in original_messages if "Here we are" in x]) == 1


def test_execute_multi_mode_loggers_with_single_logger_extra_config():
    pipeline_def, _, __ = define_multi_mode_with_loggers_pipeline()

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(
            pipeline=pipeline_def,
            mode="foo_mode",
            run_config={
                "loggers": {
                    "foo": {"config": {"log_level": "DEBUG"}},
                    "bar": {"config": {"log_level": "DEBUG"}},
                }
            },
        )


def test_execute_multi_mode_loggers_with_multiple_loggers():
    (
        pipeline_def,
        foo_logger_captured_results,
        bar_logger_captured_results,
    ) = define_multi_mode_with_loggers_pipeline()

    execute_pipeline(
        pipeline=pipeline_def,
        mode="foo_bar_mode",
        run_config={
            "loggers": {
                "foo": {"config": {"log_level": "DEBUG"}},
                "bar": {"config": {"log_level": "DEBUG"}},
            }
        },
    )

    foo_original_messages = parse_captured_results(foo_logger_captured_results)

    assert len([x for x in foo_original_messages if "Here we are" in x]) == 1

    bar_original_messages = parse_captured_results(bar_logger_captured_results)

    assert len([x for x in bar_original_messages if "Here we are" in x]) == 1


def test_execute_multi_mode_loggers_with_multiple_loggers_single_config():
    (
        pipeline_def,
        foo_logger_captured_results,
        bar_logger_captured_results,
    ) = define_multi_mode_with_loggers_pipeline()

    execute_pipeline(
        pipeline_def,
        mode="foo_bar_mode",
        run_config={"loggers": {"foo": {"config": {"log_level": "DEBUG"}}}},
    )

    foo_original_messages = parse_captured_results(foo_logger_captured_results)

    assert len([x for x in foo_original_messages if "Here we are" in x]) == 1

    assert not bar_logger_captured_results
