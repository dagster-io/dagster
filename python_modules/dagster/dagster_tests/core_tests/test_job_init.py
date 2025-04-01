import pytest
from dagster import DagsterInstance, GraphDefinition, op, resource
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context_creation_job import PlanExecutionContextManager
from dagster._core.execution.resources_init import (
    resource_initialization_event_generator,
    resource_initialization_manager,
    single_resource_event_generator,
)
from dagster._core.execution.retries import RetryMode
from dagster._core.log_manager import DagsterLogManager
from dagster._core.system_config.objects import ResolvedRunConfig


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


def gen_basic_resource_job(called=None, cleaned=None):
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

    @op(required_resource_keys={"a", "b"})
    def resource_op(_):
        pass

    return GraphDefinition(
        name="basic_resource_job",
        node_defs=[resource_op],
    ).to_job(resource_defs={"a": resource_a, "b": resource_b})


def test_clean_event_generator_exit():
    """Testing for generator cleanup
    (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
    """
    from dagster._core.definitions.resource_definition import ScopedResourcesBuilder
    from dagster._core.execution.context.init import InitResourceContext

    job_def = gen_basic_resource_job()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job_def)
    run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)
    log_manager = DagsterLogManager.create(loggers=[], dagster_run=run)
    resolved_run_config = ResolvedRunConfig.build(job_def)
    execution_plan = create_execution_plan(job_def)

    resource_name, resource_def = next(iter(job_def.resource_defs.items()))
    resource_context = InitResourceContext(
        resource_def=resource_def,
        resources=ScopedResourcesBuilder().build(None),
        all_resource_defs=job_def.resource_defs,
        resource_config=None,
        dagster_run=run,
        instance=instance,
    )
    generator = single_resource_event_generator(resource_context, resource_name, resource_def)
    next(generator)
    generator.close()

    generator = resource_initialization_event_generator(
        resource_defs=job_def.resource_defs,
        resource_configs=resolved_run_config.resources,
        log_manager=log_manager,
        execution_plan=execution_plan,
        dagster_run=run,
        resource_keys_to_init={"a"},
        instance=instance,
        emit_persistent_events=True,
        event_loop=None,
    )
    next(generator)
    generator.close()

    generator = PlanExecutionContextManager(
        job=InMemoryJob(job_def),
        execution_plan=execution_plan,
        run_config={},
        dagster_run=run,
        instance=instance,
        retry_mode=RetryMode.DISABLED,
        scoped_resources_builder_cm=resource_initialization_manager,
    ).get_generator()
    next(generator)
    generator.close()


@op
def fake_op(_):
    pass
