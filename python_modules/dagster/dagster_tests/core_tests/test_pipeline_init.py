import pytest
from dagster import (
    DagsterInstance,
    Field,
    ModeDefinition,
    PipelineDefinition,
    StringSource,
    resource,
    solid,
)
from dagster.core.definitions.intermediate_storage import IntermediateStorageDefinition
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import PlanExecutionContextManager
from dagster.core.execution.resources_init import (
    resource_initialization_event_generator,
    resource_initialization_manager,
    single_resource_event_generator,
)
from dagster.core.execution.retries import RetryMode
from dagster.core.log_manager import DagsterLogManager
from dagster.core.system_config.objects import EnvironmentConfig


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
    """Testing for generator cleanup
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
        resource_def=resource_def,
        resource_config=None,
        pipeline_run=pipeline_run,
        instance=instance,
    )
    generator = single_resource_event_generator(resource_context, resource_name, resource_def)
    next(generator)
    generator.close()

    resource_defs = pipeline_def.get_mode_definition(environment_config.mode)

    generator = resource_initialization_event_generator(
        resource_defs=resource_defs,
        resource_configs=environment_config.resources,
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


def test_intermediate_storage_run_config_not_required():
    """No run config is provided for intermediate storage defs, but none is necessary."""

    intermediate_storage_def = IntermediateStorageDefinition(
        name="test_intermediate", is_persistent=False, required_resource_keys=set()
    )
    fake_mode = ModeDefinition(
        name="fakemode",
        intermediate_storage_defs=[intermediate_storage_def],
    )
    pipeline_def = PipelineDefinition([fake_solid], name="fakename", mode_defs=[fake_mode])
    environment_config = EnvironmentConfig.build(pipeline_def, {}, mode="fakemode")
    assert environment_config.intermediate_storage.intermediate_storage_name == "test_intermediate"


def test_intermediate_storage_definition_run_config_required():
    """Run config required for intermediate storage definition, none provided to pipeline def."""

    intermediate_storage_requires_config = IntermediateStorageDefinition(
        name="test_intermediate_requires_config",
        is_persistent=False,
        required_resource_keys=set(),
        config_schema={"field": Field(StringSource)},
    )
    run_config = {
        "intermediate_storage": {
            "test_intermediate_requires_config": {"config": {"field": "value"}}
        }
    }

    fake_mode = ModeDefinition(
        name="fakemode", intermediate_storage_defs=[intermediate_storage_requires_config]
    )
    pipeline_def = PipelineDefinition([fake_solid], name="fakename", mode_defs=[fake_mode])

    environment_config = EnvironmentConfig.build(pipeline_def, run_config, mode="fakemode")

    assert (
        environment_config.intermediate_storage.intermediate_storage_name
        == "test_intermediate_requires_config"
    )

    with pytest.raises(DagsterInvalidConfigError):
        environment_config = EnvironmentConfig.build(pipeline_def, {}, mode="fakemode")
