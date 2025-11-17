from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import TYPE_CHECKING, cast

import dagster as dg
import pytest
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.execution.context.compute import ExecutionContextTypes, enter_execution_context
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.context_creation_job import scoped_job_context
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.storage.dagster_run import DagsterRun

if TYPE_CHECKING:
    from dagster._core.execution.plan.step import ExecutionStep

from dagster_tests.execution_tests.async_tests.helpers import (
    StepContextFactory,
    _create_plan_and_run,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def dagster_instance() -> Iterator[dg.DagsterInstance]:
    with dg.DagsterInstance.ephemeral() as instance:
        yield instance


@pytest.fixture
def simple_job_def() -> dg.JobDefinition:
    @dg.op
    def emit_value() -> int:
        return 1

    @dg.op
    def return_input(value: int) -> int:
        return value

    @dg.job
    def simple_job():
        return_input(emit_value())

    return simple_job


@pytest.fixture
def simple_plan_and_run(
    simple_job_def: dg.JobDefinition,
) -> tuple[ExecutionPlan, DagsterRun]:
    plan, dagster_run, _ = _create_plan_and_run(simple_job_def)
    return plan, dagster_run


@contextmanager
def _step_context_for_job(
    job_def: dg.JobDefinition,
    instance: dg.DagsterInstance,
    step_key: str | None = None,
    run_config: dict[str, object] | None = None,
) -> Iterator[StepExecutionContext]:
    plan, dagster_run, resolved_run_config = _create_plan_and_run(job_def, run_config)
    if step_key:
        step = plan.get_step_by_key(step_key)
    else:
        step = next(iter(plan.get_all_steps_in_topo_order()))
    with scoped_job_context(
        plan,
        InMemoryJob(job_def),
        resolved_run_config,
        dagster_run,
        instance,
    ) as job_context:
        yield job_context.for_step(cast("ExecutionStep", step), KnownExecutionState())


@pytest.fixture
def simple_step_context(
    simple_job_def: dg.JobDefinition, dagster_instance: dg.DagsterInstance
) -> Iterator[StepExecutionContext]:
    with _step_context_for_job(simple_job_def, dagster_instance) as context:
        yield context


@pytest.fixture
def simple_compute_context(
    simple_step_context: StepExecutionContext,
) -> Iterator[ExecutionContextTypes]:
    with enter_execution_context(simple_step_context) as compute_context:
        yield compute_context


@pytest.fixture
def asset_job_def_with_check() -> dg.JobDefinition:
    asset_key = dg.AssetKey("asset_with_check")
    check_spec = dg.AssetCheckSpec(name="asset_check", asset=asset_key)

    @dg.asset(name="asset_with_check", check_specs=[check_spec])
    def asset_with_check():
        yield dg.MaterializeResult(
            asset_key=asset_key,
            metadata={"value": 1},
            check_results=[
                dg.AssetCheckResult(
                    passed=True,
                    asset_key=asset_key,
                    check_name=check_spec.name,
                )
            ],
        )

    defs = dg.Definitions(
        assets=[asset_with_check],
        jobs=[dg.define_asset_job("asset_job_with_check")],
    )
    return defs.get_job_def("asset_job_with_check")


@pytest.fixture
def asset_step_context(
    asset_job_def_with_check: dg.JobDefinition, dagster_instance: dg.DagsterInstance
) -> Iterator[StepExecutionContext]:
    with _step_context_for_job(asset_job_def_with_check, dagster_instance) as context:
        yield context


@pytest.fixture
def asset_compute_context(
    asset_step_context: StepExecutionContext,
) -> Iterator[ExecutionContextTypes]:
    with enter_execution_context(asset_step_context) as compute_context:
        yield compute_context


@pytest.fixture
def multi_asset_job_def() -> dg.JobDefinition:
    @dg.multi_asset(
        outs={
            "asset_one": dg.AssetOut(),
            "asset_two": dg.AssetOut(),
        }
    )
    def multi_asset_op():
        return {
            "asset_one": 1,
            "asset_two": 2,
        }

    defs = dg.Definitions(
        assets=[multi_asset_op],
        jobs=[dg.define_asset_job("multi_asset_job")],
    )
    return defs.get_job_def("multi_asset_job")


@pytest.fixture
def multi_asset_step_context(
    multi_asset_job_def: dg.JobDefinition, dagster_instance: dg.DagsterInstance
) -> Iterator[StepExecutionContext]:
    with _step_context_for_job(multi_asset_job_def, dagster_instance) as context:
        yield context


@pytest.fixture
def multi_asset_compute_context(
    multi_asset_step_context: StepExecutionContext,
) -> Iterator[ExecutionContextTypes]:
    with enter_execution_context(multi_asset_step_context) as compute_context:
        yield compute_context


@pytest.fixture
def step_context_factory(dagster_instance: dg.DagsterInstance) -> StepContextFactory:
    def _factory(
        job_def: dg.JobDefinition,
        step_key: str | None = None,
        run_config: dict[str, object] | None = None,
    ) -> AbstractContextManager[StepExecutionContext]:
        return _step_context_for_job(job_def, dagster_instance, step_key, run_config)

    return _factory
