import dagster._check as check
import graphene
from dagster._core.storage.captured_log_manager import CapturedLogData
from dagster._core.storage.compute_log_manager import ComputeIOType, ComputeLogFileData

from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneComputeIOType(graphene.Enum):
    STDOUT = "stdout"
    STDERR = "stderr"

    class Meta:
        name = "ComputeIOType"


class GrapheneComputeLogFile(graphene.ObjectType):
    class Meta:
        name = "ComputeLogFile"

    path = graphene.NonNull(graphene.String)
    data = graphene.Field(
        graphene.String, description="The data output captured from step computation at query time"
    )
    cursor = graphene.NonNull(graphene.Int)
    size = graphene.NonNull(graphene.Int)
    download_url = graphene.Field(graphene.String)


def from_compute_log_file(file: ComputeLogFileData):
    check.opt_inst_param(file, "file", ComputeLogFileData)
    if not file:
        return None
    return GrapheneComputeLogFile(
        path=file.path,
        data=file.data,
        cursor=file.cursor,
        size=file.size,
        download_url=file.download_url,
    )


class GrapheneComputeLogs(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    stepKey = graphene.NonNull(graphene.String)
    stdout = graphene.Field(GrapheneComputeLogFile)
    stderr = graphene.Field(GrapheneComputeLogFile)

    class Meta:
        name = "ComputeLogs"

    def _resolve_compute_log(self, graphene_info: ResolveInfo, io_type):
        return graphene_info.context.instance.compute_log_manager.read_logs_file(
            self.runId, self.stepKey, io_type, 0
        )

    def resolve_stdout(self, graphene_info: ResolveInfo):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDOUT)

    def resolve_stderr(self, graphene_info: ResolveInfo):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDERR)


def from_captured_log_data(log_data: CapturedLogData):
    return GrapheneCapturedLogs(
        logKey=log_data.log_key,
        stdout=log_data.stdout.decode("utf-8") if log_data.stdout else None,
        stderr=log_data.stderr.decode("utf-8") if log_data.stderr else None,
        cursor=log_data.cursor,
    )


class GrapheneCapturedLogs(graphene.ObjectType):
    logKey = non_null_list(graphene.String)
    stdout = graphene.Field(graphene.String)
    stderr = graphene.Field(graphene.String)
    cursor = graphene.Field(graphene.String)

    class Meta:
        name = "CapturedLogs"


class GrapheneCapturedLogsMetadata(graphene.ObjectType):
    stdoutDownloadUrl = graphene.Field(graphene.String)
    stdoutLocation = graphene.Field(graphene.String)
    stderrDownloadUrl = graphene.Field(graphene.String)
    stderrLocation = graphene.Field(graphene.String)

    class Meta:
        name = "CapturedLogsMetadata"
