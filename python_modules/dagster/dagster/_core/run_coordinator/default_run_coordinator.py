from dagster._core.run_coordinator.sync_in_memory_run_coordinator import SyncInMemoryRunCoordinator

# for backwards compatibility, we need to keep the old DefaultRunCoordinator
DefaultRunCoordinator = SyncInMemoryRunCoordinator
