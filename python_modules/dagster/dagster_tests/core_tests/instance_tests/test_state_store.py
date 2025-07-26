import dagster as dg
import pytest
from dagster import instance_for_test
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.execution.api import create_execution_plan, execute_run_iterator
from dagster._core.storage.state_store import StateStore
from dagster._core.test_utils import create_run_for_test


@dg.op
def recon_op():
    state_store = StateStore.get_current()
    assert isinstance(state_store, StateStore)
    return "value"


@dg.job
def recon_job():
    recon_op()


def test_state_store_get_current_during_job_execution():
    """Test that StateStore.get_current() returns a valid StateStore during job execution."""
    executed_ops = []

    @dg.asset
    def test_asset():
        state_store = StateStore.get_current()
        assert isinstance(state_store, StateStore)
        executed_ops.append("test_asset")
        return "value"

    with instance_for_test() as instance:
        result = dg.materialize([test_asset], instance=instance)
        assert result.success
        assert "test_asset" in executed_ops


def test_state_store_get_current_during_asset_execution():
    """Test that StateStore.get_current() returns a valid StateStore during asset execution."""
    executed_assets = []

    @dg.asset
    def test_asset():
        state_store = StateStore.get_current()
        assert isinstance(state_store, StateStore)
        executed_assets.append("test_asset")
        return "value"

    with instance_for_test() as instance:
        result = dg.materialize([test_asset], instance=instance)
        assert result.success
        assert "test_asset" in executed_assets


def test_state_store_get_current_during_op_execution():
    """Test that StateStore.get_current() returns a valid StateStore during op execution."""
    executed_ops = []

    @dg.asset
    def test_op_asset():
        state_store = StateStore.get_current()
        assert isinstance(state_store, StateStore)
        executed_ops.append("test_op_asset")
        return "value"

    with instance_for_test() as instance:
        result = dg.materialize([test_op_asset], instance=instance)
        assert result.success
        assert "test_op_asset" in executed_ops


def test_state_store_get_current_during_reconstructable_job_execution():
    """Test that StateStore.get_current() works during reconstructable job execution."""
    with instance_for_test() as instance:
        recon_job_obj = ReconstructableJob.for_file(__file__, "recon_job")
        run = create_run_for_test(instance, job_name="recon_job")
        events = list(execute_run_iterator(recon_job_obj, run, instance))
        success_events = [event for event in events if event.event_type_value == "PIPELINE_SUCCESS"]
        assert len(success_events) > 0


def test_state_store_get_current_during_execution_plan_creation():
    """Test that StateStore.get_current() works during execution plan creation."""
    plan_created = []

    @dg.op
    def test_op():
        state_store = StateStore.get_current()
        assert isinstance(state_store, StateStore)
        plan_created.append("plan_created")
        return "value"

    @dg.job
    def test_job():
        test_op()

    with instance_for_test() as instance:
        plan = create_execution_plan(test_job, instance=instance)
        assert plan is not None


def test_state_store_missing_context_raises_check_error():
    """Test that StateStore.get_current() raises a CheckError when no StateStore is set."""
    original_current = StateStore._current  # noqa: SLF001
    StateStore._current = None  # noqa: SLF001

    try:
        with pytest.raises(Exception):
            StateStore.get_current()
    finally:
        StateStore._current = original_current  # noqa: SLF001
