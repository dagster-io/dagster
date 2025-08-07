from functools import cached_property
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from dagster._core.instance.assets.asset_domain import AssetDomain
    from dagster._core.instance.daemon.daemon_domain import DaemonDomain
    from dagster._core.instance.events.event_domain import EventDomain
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.instance.run_launcher.run_launcher_domain import RunLauncherDomain
    from dagster._core.instance.runs.run_domain import RunDomain
    from dagster._core.instance.scheduling.scheduling_domain import SchedulingDomain
    from dagster._core.instance.storage.storage_domain import StorageDomain


class DomainsMixin:
    """Mixin providing domain properties for DagsterInstance."""

    @cached_property
    def run_domain(self) -> "RunDomain":
        from dagster._core.instance.runs.run_domain import RunDomain

        return RunDomain(cast("DagsterInstance", self))

    @cached_property
    def asset_domain(self) -> "AssetDomain":
        from dagster._core.instance.assets.asset_domain import AssetDomain

        return AssetDomain(cast("DagsterInstance", self))

    @cached_property
    def event_domain(self) -> "EventDomain":
        from dagster._core.instance.events.event_domain import EventDomain

        return EventDomain(cast("DagsterInstance", self))

    @cached_property
    def scheduling_domain(self) -> "SchedulingDomain":
        from dagster._core.instance.scheduling.scheduling_domain import SchedulingDomain

        return SchedulingDomain(cast("DagsterInstance", self))

    @cached_property
    def storage_domain(self) -> "StorageDomain":
        from dagster._core.instance.storage.storage_domain import StorageDomain

        return StorageDomain(cast("DagsterInstance", self))

    @cached_property
    def run_launcher_domain(self) -> "RunLauncherDomain":
        from dagster._core.instance.run_launcher.run_launcher_domain import RunLauncherDomain

        return RunLauncherDomain(cast("DagsterInstance", self))

    @cached_property
    def daemon_domain(self) -> "DaemonDomain":
        from dagster._core.instance.daemon.daemon_domain import DaemonDomain

        return DaemonDomain(cast("DagsterInstance", self))
