import time
from typing import TYPE_CHECKING, Any, Mapping, Optional, cast

from typing_extensions import Self

import dagster._seven as seven
from dagster import (
    _check as check,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterLaunchFailedError,
    DagsterUserCodeProcessError,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import GRPC_INFO_TAG
from dagster._serdes import (
    ConfigurableClass,
    deserialize_value,
)
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils.merger import merge_dicts

from .base import LaunchRunContext, RunLauncher

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._grpc.client import DagsterGrpcClient


# note: this class is a top level export, so we defer many imports til use for performance
class DefaultRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs against running GRPC servers."""

    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._inst_data = inst_data

        self._run_ids = set()

        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return DefaultRunLauncher(inst_data=inst_data)

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
                    job_origin=run.external_job_origin,  # type: ignore  # (possible none)
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
        from dagster._core.host_representation.code_location import (
            GrpcServerCodeLocation,
        )

        run = context.dagster_run

        check.inst_param(run, "run", DagsterRun)

        if not context.workspace:
            raise DagsterInvariantViolationError(
                "DefaultRunLauncher requires a workspace to be included in its LaunchRunContext"
            )

        external_job_origin = check.not_none(run.external_job_origin)
        code_location = context.workspace.get_code_location(
            external_job_origin.external_repository_origin.code_location_origin.location_name
        )

        check.inst(
            code_location,
            GrpcServerCodeLocation,
            "DefaultRunLauncher: Can't launch runs for pipeline not loaded from a GRPC server",
        )

        DefaultRunLauncher.launch_run_from_grpc_client(
            self._instance, run, cast(GrpcServerCodeLocation, code_location).client
        )

        self._run_ids.add(run.run_id)

    def _get_grpc_client_for_termination(self, run_id):
        # defer for perf
        from dagster._grpc.client import DagsterGrpcClient

        if not self.has_instance:
            return None

        run = self._instance.get_run_by_id(run_id)
        if not run or run.is_finished:
            return None

        tags = run.tags

        if GRPC_INFO_TAG not in tags:
            return None

        grpc_info = seven.json.loads(tags.get(GRPC_INFO_TAG))

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
        if not run:
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
                    and not self._instance.get_run_by_id(run_id).is_finished
                )
            ]

            if len(active_run_ids) == 0:
                return

            if total_time >= timeout:
                raise Exception(f"Timed out waiting for these runs to finish: {active_run_ids!r}")

            total_time += interval
            time.sleep(interval)
            interval = interval * 2
