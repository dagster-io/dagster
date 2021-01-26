import graphene
from dagster import check
from dagster.core.storage.compute_log_manager import ComputeIOType, ComputeLogFileData


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


def from_compute_log_file(_graphene_info, file):
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

    def _resolve_compute_log(self, graphene_info, io_type):
        return graphene_info.context.instance.compute_log_manager.read_logs_file(
            self.runId, self.stepKey, io_type, 0
        )

    def resolve_stdout(self, graphene_info):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDOUT)

    def resolve_stderr(self, graphene_info):
        return self._resolve_compute_log(graphene_info, ComputeIOType.STDERR)
