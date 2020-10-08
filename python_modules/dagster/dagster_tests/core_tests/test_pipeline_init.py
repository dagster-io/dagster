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
from dagster.core.definitions.system_storage import SystemStorageDefinition
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import PipelineExecutionContextManager
from dagster.core.execution.resources_init import (
    resource_initialization_event_generator,
    resource_initialization_manager,
    single_resource_event_generator,
)
from dagster.core.log_manager import DagsterLogManager
from dagster.core.system_config.objects import (
    EmptyIntermediateStoreBackcompatConfig,
    EnvironmentConfig,
)
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


@solid
def fake_solid(_):
    pass


def test_default_storage_no_run_config():
    """Test default storage for pipeline when no run config is provided."""

    fake_mode_in_mem = ModeDefinition(
        name="fakemodeinmem", intermediate_storage_defs=[], system_storage_defs=[]
    )
    pipeline_def_in_mem = PipelineDefinition(
        [fake_solid], name="fakename", mode_defs=[fake_mode_in_mem]
    )
    environment_config_local = EnvironmentConfig.build(
        pipeline_def_in_mem, {}, mode="fakemodeinmem"
    )

    # The default intermediate_storage_defs for any mode is the list [in_memory, filesystem].
    # If no run_config is provided, should default to the first, which is in_memory
    assert environment_config_local.intermediate_storage.intermediate_storage_name == "in_memory"
    assert environment_config_local.storage.system_storage_name == "in_memory"


def test_system_storage_run_config_not_required():
    """No run config is provided for system storage defs, but none is necessary."""

    system_storage_def = SystemStorageDefinition(
        name="test_system", is_persistent=False, required_resource_keys=set()
    )
    fake_mode = ModeDefinition(name="fakemode", system_storage_defs=[system_storage_def],)
    pipeline_def = PipelineDefinition([fake_solid], name="fakename", mode_defs=[fake_mode])
    environment_config = EnvironmentConfig.build(pipeline_def, {}, mode="fakemode")
    assert environment_config.storage.system_storage_name == "test_system"


def test_intermediate_storage_run_config_not_required():
    """No run config is provided for intermediate storage defs, but none is necessary."""

    intermediate_storage_def = IntermediateStorageDefinition(
        name="test_intermediate", is_persistent=False, required_resource_keys=set()
    )
    fake_mode = ModeDefinition(
        name="fakemode", intermediate_storage_defs=[intermediate_storage_def],
    )
    pipeline_def = PipelineDefinition([fake_solid], name="fakename", mode_defs=[fake_mode])
    environment_config = EnvironmentConfig.build(pipeline_def, {}, mode="fakemode")
    assert environment_config.intermediate_storage.intermediate_storage_name == "test_intermediate"


def test_backcompat_intermediate_storage_config():
    """Run config provided for system storage; backcompatibility for intermediate storage."""

    fake_mode = ModeDefinition(name="fakemode")
    system_storage_config = {"storage": {"filesystem": {}}}
    pipeline_def = PipelineDefinition([fake_solid], name="fakename", mode_defs=[fake_mode])
    environment_config = EnvironmentConfig.build(
        pipeline_def, system_storage_config, mode="fakemode"
    )
    assert isinstance(
        environment_config.intermediate_storage.intermediate_storage_name,
        EmptyIntermediateStoreBackcompatConfig,
    )
    assert environment_config.storage.system_storage_name == "filesystem"


def test_system_storage_definition_run_config_required():
    """Run config required for system storage definition, none provided to pipeline def."""

    system_storage_requires_config = SystemStorageDefinition(
        name="test_system_requires_config",
        is_persistent=False,
        required_resource_keys=set(),
        config_schema={"field": Field(StringSource)},
    )
    run_config = {"storage": {"test_system_requires_config": {"config": {"field": "value"}}}}

    fake_mode = ModeDefinition(
        name="fakemode", system_storage_defs=[system_storage_requires_config]
    )
    pipeline_def = PipelineDefinition([fake_solid], name="fakename", mode_defs=[fake_mode])

    environment_config = EnvironmentConfig.build(pipeline_def, run_config, mode="fakemode")

    assert environment_config.storage.system_storage_name == "test_system_requires_config"

    with pytest.raises(DagsterInvalidConfigError):
        environment_config = EnvironmentConfig.build(pipeline_def, {}, mode="fakemode")


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
