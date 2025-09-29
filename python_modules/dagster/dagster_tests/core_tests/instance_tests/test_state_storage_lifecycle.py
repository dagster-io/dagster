import asyncio

import dagster as dg
import pytest
from dagster import instance_for_test
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.execution.api import create_execution_plan, execute_run_iterator
from dagster._core.storage.defs_state import DefsStateStorage
from dagster._core.test_utils import create_run_for_test
from dagster._utils.cached_method import cached_method


@dg.op
def recon_op():
    state_store = DefsStateStorage.get()
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
        state_storage = DefsStateStorage.get()
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
        state_storage = DefsStateStorage.get()
        assert isinstance(state_storage, DefsStateStorage)
        plan_created.append("plan_created")
        return "value"

    @dg.job
    def test_job():
        test_op()

    with instance_for_test():
        plan = create_execution_plan(test_job)
        assert plan is not None


def test_defs_state_storage_get_current_after_init_resource_context():
    with instance_for_test() as instance:
        expected_storage = instance.defs_state_storage
        assert DefsStateStorage.get() is expected_storage

        with dg.build_init_resource_context():
            # ends up being None in here because an ephemeral instance is created
            assert DefsStateStorage.get() is None

        # no longer None once we leave the context
        assert DefsStateStorage.get() is expected_storage

        with dg.build_init_resource_context(instance=instance):
            # if we pass the instance in, the state storage is the same
            assert DefsStateStorage.get() is expected_storage

        assert DefsStateStorage.get() is expected_storage

    # once the instance is disposed, the state storage is None
    assert DefsStateStorage.get() is None


def test_defs_state_storage_get_current_after_configurable_resouce():
    class Holder:
        def __init__(self, stuff: tuple):
            self.stuff = stuff

    class AResource(dg.ConfigurableResource):
        foo: str

        # use cached_method to avoid garbage collection
        @cached_method
        def get_some_val(self) -> Holder:
            with self.process_config_and_initialize_cm() as initialized:
                # include initialized so that __del__ is not called on it
                # once we return from this function
                return Holder(stuff=(self.foo + "baz", initialized))

    with instance_for_test() as instance:
        expected_storage = instance.defs_state_storage
        assert DefsStateStorage.get() is expected_storage

        resource = AResource(foo="bar")
        assert resource.get_some_val().stuff[0] == "barbaz"

        # should not have changed after get_some_val is called
        assert DefsStateStorage.get() is expected_storage

    assert DefsStateStorage.get() is None


def test_state_storage_disposed() -> None:
    with instance_for_test():
        assert DefsStateStorage.get() is not None
    assert DefsStateStorage.get() is None


@pytest.mark.asyncio
async def test_instance_with_manual_async_context_switching():
    """Simulates a scenario that can happen when an instance is entered in an async webserver context."""

    async def startup_in_task():
        instance_cm = instance_for_test()
        instance = instance_cm.__enter__()
        instance.__enter__()
        assert DefsStateStorage.get() is instance.defs_state_storage
        return instance_cm, instance

    async def shutdown_in_different_task(instance_cm, instance):
        instance.__exit__(None, None, None)  # This should not fail
        instance_cm.__exit__(None, None, None)

    # startup in one task
    startup_task = asyncio.create_task(startup_in_task())
    instance_cm, instance = await startup_task

    # shutdown in a different task
    shutdown_task = asyncio.create_task(shutdown_in_different_task(instance_cm, instance))
    await shutdown_task

    # should just set the value to None instead of erroring
    assert DefsStateStorage.get() is None

    # everything should still work going forward
    with instance_for_test() as instance:
        assert DefsStateStorage.get() is instance.defs_state_storage
    assert DefsStateStorage.get() is None
