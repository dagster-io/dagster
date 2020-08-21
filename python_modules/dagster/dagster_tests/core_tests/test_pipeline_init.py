import pytest

from dagster import DagsterInstance, ModeDefinition, PipelineDefinition, resource, solid
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import PipelineExecutionContextManager
from dagster.core.execution.resources_init import (
    resource_initialization_event_generator,
    resource_initialization_manager,
    single_resource_event_generator,
)
from dagster.core.log_manager import DagsterLogManager
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.utils import make_new_run_id


def test_generator_exit():
    def generator():
        try:
            yield "A"
        finally:
            yield "EXIT"

    gen = generator()
    next(gen)
    with pytest.raises(RuntimeError, match="generator ignored GeneratorExit"):
        gen.close()


def gen_basic_resource_pipeline(called=None, cleaned=None):
    if not called:
        called = []

    if not cleaned:
        cleaned = []

    @resource
    def resource_a(_):
        try:
            called.append("A")
            yield "A"
        finally:
            cleaned.append("A")

    @resource
    def resource_b(_):
        try:
            called.append("B")
            yield "B"
        finally:
            cleaned.append("B")

    @solid(required_resource_keys={"a", "b"})
    def resource_solid(_):
        pass

    return PipelineDefinition(
        name="basic_resource_pipeline",
        solid_defs=[resource_solid],
        mode_defs=[ModeDefinition(resource_defs={"a": resource_a, "b": resource_b})],
    )


def test_clean_event_generator_exit():
    """ Testing for generator cleanup
    (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/)
    """
    from dagster.core.execution.context.init import InitResourceContext

    pipeline_def = gen_basic_resource_pipeline()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline_def)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def, execution_plan=execution_plan
    )
    log_manager = DagsterLogManager(run_id=pipeline_run.run_id, logging_tags={}, loggers=[])
    environment_config = EnvironmentConfig.build(pipeline_def)
    execution_plan = create_execution_plan(pipeline_def)

    resource_name, resource_def = next(iter(pipeline_def.get_default_mode().resource_defs.items()))
    resource_context = InitResourceContext(
        pipeline_def=pipeline_def,
        resource_def=resource_def,
        resource_config=None,
        run_id=make_new_run_id(),
    )
    generator = single_resource_event_generator(resource_context, resource_name, resource_def)
    next(generator)
    generator.close()

    generator = resource_initialization_event_generator(
        execution_plan, environment_config, pipeline_run, log_manager, {"a"}
    )
    next(generator)
    generator.close()

    generator = PipelineExecutionContextManager(  # pylint: disable=protected-access
        execution_plan, {}, pipeline_run, instance, resource_initialization_manager,
    ).get_generator()
    next(generator)
    generator.close()
