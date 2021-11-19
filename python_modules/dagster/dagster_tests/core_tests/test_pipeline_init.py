import pytest
from dagster import DagsterInstance, ModeDefinition, PipelineDefinition, resource, solid
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import PlanExecutionContextManager
from dagster.core.execution.resources_init import (
    resource_initialization_event_generator,
    resource_initialization_manager,
    single_resource_event_generator,
)
from dagster.core.execution.retries import RetryMode
from dagster.core.log_manager import DagsterLogManager
from dagster.core.system_config.objects import ResolvedRunConfig


def test_generator_exit():
    def generator():
        try:
            yield "A"
        finally:
            yield "EXIT"  # pylint: disable=finally-yield

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
    def resource_a():
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
    """Testing for generator cleanup
    (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/)
    """
    from dagster.core.execution.context.init import InitResourceContext
    from dagster.core.definitions.resource_definition import ScopedResourcesBuilder

    pipeline_def = gen_basic_resource_pipeline()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline_def)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def, execution_plan=execution_plan
    )
    log_manager = DagsterLogManager.create(loggers=[], pipeline_run=pipeline_run)
    resolved_run_config = ResolvedRunConfig.build(pipeline_def)
    execution_plan = create_execution_plan(pipeline_def)

    resource_name, resource_def = next(iter(pipeline_def.get_default_mode().resource_defs.items()))
    resource_context = InitResourceContext(
        resource_def=resource_def,
        resources=ScopedResourcesBuilder().build(None),
        resource_config=None,
        pipeline_run=pipeline_run,
        instance=instance,
    )
    generator = single_resource_event_generator(resource_context, resource_name, resource_def)
    next(generator)
    generator.close()

    resource_defs = pipeline_def.get_mode_definition(resolved_run_config.mode)

    generator = resource_initialization_event_generator(
        resource_defs=resource_defs,
        resource_configs=resolved_run_config.resources,
        log_manager=log_manager,
        execution_plan=execution_plan,
        pipeline_run=pipeline_run,
        resource_keys_to_init={"a"},
        instance=instance,
        emit_persistent_events=True,
        pipeline_def_for_backwards_compat=pipeline_def,
    )
    next(generator)
    generator.close()

    generator = PlanExecutionContextManager(  # pylint: disable=protected-access
        pipeline=InMemoryPipeline(pipeline_def),
        execution_plan=execution_plan,
        run_config={},
        pipeline_run=pipeline_run,
        instance=instance,
        retry_mode=RetryMode.DISABLED,
        scoped_resources_builder_cm=resource_initialization_manager,
    ).get_generator()
    next(generator)
    generator.close()


@solid
def fake_solid(_):
    pass
