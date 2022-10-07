from typing import List

from graphene import ResolveInfo

from dagster._core.storage.captured_log_manager import CapturedLogManager


def get_captured_log_metadata(graphene_info: ResolveInfo, log_key: List[str]):
    from ..schema.logs.compute_logs import GrapheneCapturedLogsMetadata

    if not isinstance(graphene_info.context.instance.compute_log_manager, CapturedLogManager):
        return GrapheneCapturedLogsMetadata()

    metadata = graphene_info.context.instance.compute_log_manager.get_log_metadata(log_key)
    return GrapheneCapturedLogsMetadata(
        stdoutDownloadUrl=metadata.stdout_download_url,
        stdoutLocation=metadata.stdout_location,
        stderrDownloadUrl=metadata.stderr_download_url,
        stderrLocation=metadata.stderr_location,
    )
