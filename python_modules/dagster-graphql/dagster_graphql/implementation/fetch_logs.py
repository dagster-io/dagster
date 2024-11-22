from collections.abc import Sequence
from typing import TYPE_CHECKING

from dagster_graphql.schema.util import ResolveInfo

if TYPE_CHECKING:
    from dagster_graphql.schema.logs.compute_logs import GrapheneCapturedLogsMetadata


def get_captured_log_metadata(
    graphene_info: ResolveInfo, log_key: Sequence[str]
) -> "GrapheneCapturedLogsMetadata":
    from dagster_graphql.schema.logs.compute_logs import GrapheneCapturedLogsMetadata

    metadata = graphene_info.context.instance.compute_log_manager.get_log_metadata(log_key)
    return GrapheneCapturedLogsMetadata(
        stdoutDownloadUrl=metadata.stdout_download_url,
        stdoutLocation=metadata.stdout_location,
        stderrDownloadUrl=metadata.stderr_download_url,
        stderrLocation=metadata.stderr_location,
    )
