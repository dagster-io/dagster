from dagster._core.run_coordinator.immediately_launch_run_coordinator import (
    ImmediatelyLaunchRunCoordinator,
)

# for backwards compatibility, we need to keep the old DefaultRunCoordinator
DefaultRunCoordinator = ImmediatelyLaunchRunCoordinator
