import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution import resources_init
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context_creation_job import PlanExecutionContextManager
from dagster._core.execution.resources_init import (
    get_required_resource_keys_to_init,
    get_resource_origins_mapping,
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

    @dg.resource
    def resource_a():
        try:
            called.append("A")
            yield "A"
        finally:
            cleaned.append("A")

    @dg.resource
    def resource_b(_):
        try:
            called.append("B")
            yield "B"
        finally:
            cleaned.append("B")

    @dg.op(required_resource_keys={"a", "b"})
    def resource_op(_):
        pass

    return dg.GraphDefinition(
        name="basic_resource_job",
        node_defs=[resource_op],
    ).to_job(resource_defs={"a": resource_a, "b": resource_b})


def test_clean_event_generator_exit():
    """Testing for generator cleanup
    (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
    """
    from dagster._core.definitions.resource_definition import ScopedResourcesBuilder

    job_def = gen_basic_resource_job()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job_def)
    run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)
    log_manager = DagsterLogManager.create(loggers=[], dagster_run=run)
    resolved_run_config = ResolvedRunConfig.build(job_def)
    execution_plan = create_execution_plan(job_def)

    resource_name, resource_def = next(iter(job_def.resource_defs.items()))
    resource_context = dg.InitResourceContext(
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


@dg.op
def fake_op(_):
    pass


def test_get_resource_origins_mapping():
    @dg.resource
    def spark(_):
        return "spark"

    @dg.resource(required_resource_keys={"spark"})
    def pyspark(_):
        return "pyspark"

    @dg.resource
    def required_by_nobody(_):
        return "nobody"

    @dg.op(required_resource_keys={"pyspark"})
    def uses_pyspark(_):
        pass

    @dg.op(required_resource_keys={"spark"})
    def uses_spark_directly(_):
        pass

    @dg.graph
    def nested():
        uses_spark_directly()

    @dg.job(
        resource_defs={
            "spark": spark,
            "pyspark": pyspark,
            "required_by_nobody": required_by_nobody,
        }
    )
    def origins_job():
        uses_pyspark()
        nested()

    mapping = get_resource_origins_mapping(origins_job)

    assert mapping["pyspark"] == {"uses_pyspark"}

    # spark is required transitively (via pyspark) and directly by a nested op, reported by handle
    assert mapping["spark"] == {"uses_pyspark", "nested.uses_spark_directly"}

    # resources no op requires are absent from the mapping
    assert "required_by_nobody" not in mapping
    assert "io_manager" not in mapping


def gen_two_op_resource_job():
    """A job where each op requires a different resource."""

    @dg.resource
    def resource_a(_):
        return "a"

    @dg.resource
    def resource_b(_):
        return "b"

    @dg.op(required_resource_keys={"resource_a"})
    def op_one(_):
        pass

    @dg.op(required_resource_keys={"resource_b"})
    def op_two(_):
        pass

    @dg.job(resource_defs={"resource_a": resource_a, "resource_b": resource_b})
    def two_op_resource_job():
        op_one()
        op_two()

    return two_op_resource_job


def _resource_init_started_message(job_def, *, pass_job_def: bool) -> str:
    """Drives the real resource-init generator and returns the RESOURCE_INIT_STARTED message."""
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job_def)
    run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)
    log_manager = DagsterLogManager.create(loggers=[], dagster_run=run)
    resolved_run_config = ResolvedRunConfig.build(job_def)

    events = list(
        resource_initialization_event_generator(
            resource_defs=job_def.resource_defs,
            resource_configs=resolved_run_config.resources,
            log_manager=log_manager,
            execution_plan=execution_plan,
            dagster_run=run,
            resource_keys_to_init=get_required_resource_keys_to_init(execution_plan, job_def),
            instance=instance,
            emit_persistent_events=True,
            event_loop=None,
            job_def=job_def if pass_job_def else None,
        )
    )

    started = [
        event
        for event in events
        if isinstance(event, DagsterEvent)
        and event.event_type_value == DagsterEventType.RESOURCE_INIT_STARTED.value
    ]
    assert len(started) == 1, f"expected exactly one RESOURCE_INIT_STARTED, got {len(started)}"
    return started[0].message


def test_resource_init_message_reports_op_origins():
    """With job_def available, the message says which ops require each resource (issue #2307)."""
    message = _resource_init_started_message(gen_two_op_resource_job(), pass_job_def=True)

    assert message == (
        "Starting initialization of resources:\n"
        "io_manager - required by the I/O layer\n"
        "resource_a - required by op instances [op_one]\n"
        "resource_b - required by op instances [op_two]"
    )


def test_resource_init_message_falls_back_without_job_def():
    """Without job_def (e.g. build_resources), the message is byte-for-byte the original."""
    message = _resource_init_started_message(gen_two_op_resource_job(), pass_job_def=False)

    assert message == "Starting initialization of resources [io_manager, resource_a, resource_b]."


def test_job_def_reaches_innermost_resource_generator(monkeypatch):
    """job_def must be forwarded from resource_initialization_manager down to the innermost
    generator. A param that is accepted but not forwarded still typechecks, so assert it arrives.
    """
    job_def = gen_two_op_resource_job()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job_def)
    run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)
    log_manager = DagsterLogManager.create(loggers=[], dagster_run=run)
    resolved_run_config = ResolvedRunConfig.build(job_def)

    captured = {}
    real_core_generator = resources_init._core_resource_initialization_event_generator  # noqa: SLF001

    def spy(**kwargs):
        captured["job_def"] = kwargs.get("job_def", "<<not forwarded>>")
        return real_core_generator(**kwargs)

    monkeypatch.setattr(resources_init, "_core_resource_initialization_event_generator", spy)

    manager = resource_initialization_manager(
        resource_defs=job_def.resource_defs,
        resource_configs=resolved_run_config.resources,
        log_manager=log_manager,
        execution_plan=execution_plan,
        dagster_run=run,
        resource_keys_to_init=get_required_resource_keys_to_init(execution_plan, job_def),
        instance=instance,
        emit_persistent_events=True,
        event_loop=None,
        job_def=job_def,
    )
    list(manager.generate_setup_events())

    assert captured["job_def"] is job_def
