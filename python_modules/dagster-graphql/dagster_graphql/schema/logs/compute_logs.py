import graphene
from dagster._core.storage.compute_log_manager import CapturedLogData

from dagster_graphql.schema.util import non_null_list


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
