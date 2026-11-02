import time
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

import dagster_shared.seven as seven
from typing_extensions import Self

from dagster import _check as check
from dagster._annotations import public
from dagster._config.config_schema import UserConfigSchema
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterLaunchFailedError,
    DagsterUserCodeProcessError,
)
from dagster._core.launcher.base import LaunchRunContext, RunLauncher
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import GRPC_INFO_TAG
from dagster._serdes import ConfigurableClass, deserialize_value
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._grpc.client import DagsterGrpcClient


# note: this class is a top level export, so we defer many imports til use for performance
@public
class DefaultRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs against running GRPC servers."""

    def __init__(
        self,
        inst_data: ConfigurableClassData | None = None,
    ):
        self._inst_data = inst_data

        self._run_ids = set()

        super().__init__()

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data)

    @staticmethod
    def launch_run_from_grpc_client(
        instance: "DagsterInstance", run: DagsterRun, grpc_client: "DagsterGrpcClient"
    ):
        # defer for perf
        from dagster._grpc.types import ExecuteExternalJobArgs, StartRunResult

        instance.add_run_tags(
            run.run_id,
            {
                GRPC_INFO_TAG: seven.json.dumps(
                    merge_dicts(
                        {"host": grpc_client.host},
                        (
                            {"port": grpc_client.port}
                            if grpc_client.port
                            else {"socket": grpc_client.socket}
                        ),
                        ({"use_ssl": True} if grpc_client.use_ssl else {}),
                    )
                )
            },
        )

        res = deserialize_value(
            grpc_client.start_run(
                ExecuteExternalJobArgs(
                    job_origin=run.remote_job_origin,  # type: ignore  # (possible none)
                    run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                )
            ),
            StartRunResult,
        )
        if not res.success:
            raise (
                DagsterLaunchFailedError(
                    res.message, serializable_error_info=res.serializable_error_info
                )
            )

    def launch_run(self, context: LaunchRunContext) -> None:
        # defer for perf
        from dagster._core.remote_representation.code_location import GrpcServerCodeLocation

        run = context.dagster_run

        check.inst_param(run, "run", DagsterRun)

        if not context.workspace:
            raise DagsterInvariantViolationError(
                "DefaultRunLauncher requires a workspace to be included in its LaunchRunContext"
            )

        remote_job_origin = check.not_none(run.remote_job_origin)
        code_location = context.workspace.get_code_location(
            remote_job_origin.repository_origin.code_location_origin.location_name
        )

        check.inst(
            code_location,
            GrpcServerCodeLocation,
            "DefaultRunLauncher: Can't launch runs for pipeline not loaded from a GRPC server",
        )

        DefaultRunLauncher.launch_run_from_grpc_client(
            self._instance, run, cast("GrpcServerCodeLocation", code_location).client
        )

        self._run_ids.add(run.run_id)

    def _get_grpc_client_for_termination(self, run_id):
        if not self.has_instance:
            return None
        return self._get_grpc_client_for_run(self._instance.get_run_by_id(run_id))

    def _get_grpc_client_for_run(self, run: DagsterRun | None) -> "DagsterGrpcClient | None":
        # defer for perf
        from dagster._grpc.client import DagsterGrpcClient

        if not run or run.is_finished or GRPC_INFO_TAG not in run.tags:
            return None
        grpc_info = seven.json.loads(run.tags[GRPC_INFO_TAG])
        return DagsterGrpcClient(
            port=grpc_info.get("port"),
            socket=grpc_info.get("socket"),
            host=grpc_info.get("host"),
            use_ssl=bool(grpc_info.get("use_ssl", False)),
        )

    def terminate(self, run_id):
        # defer for perf
        from dagster._grpc.types import CancelExecutionRequest, CancelExecutionResult

        check.str_param(run_id, "run_id")
        if not self.has_instance:
            return False

        run = self._instance.get_run_by_id(run_id)
        if not run or run.is_finished:
            return False

        self._instance.report_run_canceling(run)

        client = self._get_grpc_client_for_termination(run_id)

        if not client:
            self._instance.report_engine_event(
                message="Unable to get grpc client to send termination request to.",
                dagster_run=run,
                cls=self.__class__,
            )
            return False

        res = deserialize_value(
            client.cancel_execution(CancelExecutionRequest(run_id=run_id)), CancelExecutionResult
        )

        if res.serializable_error_info:
            raise DagsterUserCodeProcessError.from_error_info(res.serializable_error_info)

        return res.success

    def terminate_runs(self, run_ids: Sequence[str]) -> Mapping[str, bool]:
        from dagster._grpc.types import MAX_CANCEL_EXECUTIONS_BATCH_SIZE

        check.sequence_param(run_ids, "run_ids", of_type=str)
        run_ids = list(dict.fromkeys(run_ids))
        # Preserve bound-instance overrides as well as subclass customizations. In
        # particular, custom clients may carry different authorization metadata.
        if any(
            getattr(getattr(self, name), "__func__", None) is not getattr(DefaultRunLauncher, name)
            for name in (
                "terminate",
                "_get_grpc_client_for_termination",
                "_get_grpc_client_for_run",
            )
        ):
            return super().terminate_runs(run_ids)
        if not run_ids or not self.has_instance:
            return {run_id: False for run_id in run_ids}

        current_runs: dict[str, DagsterRun] = {}
        for offset in range(0, len(run_ids), MAX_CANCEL_EXECUTIONS_BATCH_SIZE):
            current_runs.update(
                {
                    run.run_id: run
                    for run in self._instance.get_runs(
                        RunsFilter(
                            run_ids=run_ids[offset : offset + MAX_CANCEL_EXECUTIONS_BATCH_SIZE]
                        )
                    )
                }
            )
        results = {run_id: False for run_id in run_ids}
        groups: dict[
            tuple[str | None, int | None, str | None, bool],
            tuple[DagsterGrpcClient, list[DagsterRun]],
        ] = {}
        for run_id in run_ids:
            run = current_runs.get(run_id)
            if not run or run.is_finished:
                continue
            client = self._get_grpc_client_for_run(run)
            if client is None:
                # Preserve existing status and diagnostic reporting for missing clients.
                results[run_id] = self.terminate(run_id)
                continue
            key = (client.host, client.port, client.socket, client.use_ssl)
            if key not in groups:
                groups[key] = (client, [])
            groups[key][1].append(run)

        for client, runs in groups.values():
            # Bound request size even for callers other than the backfill daemon.
            for offset in range(0, len(runs), MAX_CANCEL_EXECUTIONS_BATCH_SIZE):
                page: list[DagsterRun] = []
                try:
                    for run in runs[offset : offset + MAX_CANCEL_EXECUTIONS_BATCH_SIZE]:
                        # Metadata is loaded in bulk, but preserve the single-run path's fresh
                        # terminal check immediately before reporting cancellation.
                        current = self._instance.get_run_by_id(run.run_id)
                        if not current or current.is_finished:
                            continue
                        if current.tags.get(GRPC_INFO_TAG) != run.tags.get(GRPC_INFO_TAG):
                            results[run.run_id] = self.terminate(run.run_id)
                            continue
                        try:
                            self._instance.report_run_canceling(current)
                        except BaseException:
                            # Reporting can fail after persisting CANCELING (for example,
                            # in a listener). Include that run in the first-send drain too.
                            latest = self._instance.get_run_by_id(current.run_id)
                            if latest and latest.status == DagsterRunStatus.CANCELING:
                                page.append(latest)
                            raise
                        else:
                            page.append(current)
                finally:
                    # A later preparation failure must not leave earlier runs CANCELING
                    # without ever sending their requests. This is a first send, not a retry.
                    if page:
                        response = client.cancel_executions([run.run_id for run in page])
                        for run in page:
                            result = response.results[run.run_id]
                            if result.serializable_error_info:
                                raise DagsterUserCodeProcessError.from_error_info(
                                    result.serializable_error_info
                                )
                            results[run.run_id] = result.success
        return results

    def join(self, timeout=30):
        # If this hasn't been initialized at all, we can just do a noop
        if not self.has_instance:
            return

        total_time = 0
        interval = 0.01

        while True:
            active_run_ids = [
                run_id
                for run_id in self._run_ids
                if (
                    self._instance.get_run_by_id(run_id)
                    and not self._instance.get_run_by_id(run_id).is_finished  # ty: ignore[unresolved-attribute]
                )
            ]

            if len(active_run_ids) == 0:
                return

            if total_time >= timeout:
                raise Exception(f"Timed out waiting for these runs to finish: {active_run_ids!r}")

            total_time += interval
            time.sleep(interval)
            interval = interval * 2
