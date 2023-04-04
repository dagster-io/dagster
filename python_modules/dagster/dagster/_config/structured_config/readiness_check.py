import logging
import sys
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Optional, cast

import pendulum

import dagster._check as check
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.execution.context.init import build_init_resource_context
from dagster._core.execution.resources_init import get_transitive_required_resource_keys
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._core.host_representation.external import ExternalResource
    from dagster._core.scheduler.instigation import InstigatorTick, TickStatus
    from dagster._grpc.types import ResourceReadinessCheckResult


@whitelist_for_serdes
class ReadinessCheckStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@whitelist_for_serdes
class ReadinessCheckResult(NamedTuple):
    status: ReadinessCheckStatus
    message: Optional[str]

    @classmethod
    def success(cls, message: Optional[str] = None):
        """Create a successful readiness check result."""
        return cls(ReadinessCheckStatus.SUCCESS, message)

    @classmethod
    def failure(cls, message: Optional[str] = None):
        """Create a failed readiness check result."""
        return cls(ReadinessCheckStatus.FAILURE, message)


class ReadinessCheckedResource:
    def readiness_check(self) -> ReadinessCheckResult:
        raise NotImplementedError()


class _ResourceReadinessCheckContext:
    def __init__(
        self,
        external_resource: "ExternalResource",
        tick: "InstigatorTick",
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._external_resource = external_resource
        self._instance = instance
        self._logger = logger
        self._tick = tick
        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

    @property
    def failure_count(self) -> int:
        return self._tick.tick_data.failure_count

    def update_state(
        self, status: "TickStatus", error: Optional[SerializableErrorInfo] = None, **kwargs
    ) -> None:
        skip_reason = kwargs.get("skip_reason")
        if "skip_reason" in kwargs:
            del kwargs["skip_reason"]

        self._tick = self._tick.with_status(status=status, error=error, **kwargs)

        if skip_reason:
            self._tick = self._tick.with_reason(skip_reason=skip_reason)

    def update_cursor(self, cursor: Optional[str]) -> None:
        self._tick = self._tick.with_cursor(cursor)

    def add_run_info(self, run_id=None, run_key=None) -> None:
        self._tick = self._tick.with_run_info(run_id, run_key)

    def add_log_key(self, log_key) -> None:
        self._tick = self._tick.with_log_key(log_key)

    def _write(self) -> None:
        self._instance.update_tick(self._tick)

    def __enter__(self) -> "_ResourceReadinessCheckContext":
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self._write()
        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                self._external_resource.get_external_origin_id(),
                selector_id=self._external_resource.name,
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
            )


def launch_resource_readiness_check(
    repo_def: RepositoryDefinition,
    instance_ref: Optional[InstanceRef],
    resource_name: str,
) -> "ResourceReadinessCheckResult":
    from dagster._grpc.types import ResourceReadinessCheckResult

    serializable_error_info = None
    response = ReadinessCheckResult(
        ReadinessCheckStatus.FAILURE, "Error executing readiness_check check"
    )

    try:
        with DagsterInstance.from_ref(check.not_none(instance_ref)) as instance:
            required_resource_keys = get_transitive_required_resource_keys(
                {resource_name}, repo_def.get_top_level_resources()
            )
            resources_to_build = {
                k: v
                for k, v in repo_def.get_top_level_resources().items()
                if k in required_resource_keys
            }

            res_context = build_init_resource_context(
                instance=instance, resources=resources_to_build
            )
            resource = cast(ReadinessCheckedResource, getattr(res_context.resources, resource_name))
            response = resource.readiness_check()

    except Exception:
        serializable_error_info = serializable_error_info_from_exc_info(sys.exc_info())

    return ResourceReadinessCheckResult(
        response=response, serializable_error_info=serializable_error_info
    )
