from dagster._core.run_coordinator.synchronous_run_coordinator import SynchronousRunCoordinator

# for backwards compatibility, we need to keep the old DefaultRunCoordinator
DefaultRunCoordinator = SynchronousRunCoordinator
