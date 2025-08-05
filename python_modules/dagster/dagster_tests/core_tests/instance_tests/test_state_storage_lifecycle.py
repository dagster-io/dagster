import dagster as dg
from dagster import instance_for_test
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.execution.api import create_execution_plan, execute_run_iterator
from dagster._core.storage.defs_state import DefsStateStorage
from dagster._core.test_utils import create_run_for_test


@dg.op
def recon_op():
    state_store = DefsStateStorage.get_current()
    assert isinstance(state_store, DefsStateStorage)
    return "value"


@dg.job
def recon_job():
    recon_op()


def test_state_store_get_current_during_asset_execution():
    """Test that StateStore.get_current() returns a valid StateStore during asset execution."""
    executed_assets = []

    @dg.asset
    def test_asset():
        state_storage = DefsStateStorage.get_current()
        assert isinstance(state_storage, DefsStateStorage)
        executed_assets.append("test_asset")
        return "value"

    with instance_for_test() as instance:
        result = dg.materialize([test_asset], instance=instance)
        assert result.success
        assert "test_asset" in executed_assets


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
        state_storage = DefsStateStorage.get_current()
        assert isinstance(state_storage, DefsStateStorage)
        plan_created.append("plan_created")
        return "value"

    @dg.job
    def test_job():
        test_op()

    with instance_for_test():
        plan = create_execution_plan(test_job)
        assert plan is not None


def test_state_storage_disposed() -> None:
    with instance_for_test():
        assert DefsStateStorage.get_current() is not None
    assert DefsStateStorage.get_current() is None
