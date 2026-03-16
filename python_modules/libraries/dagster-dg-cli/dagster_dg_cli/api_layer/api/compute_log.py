"""Compute logs API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.compute_log import (
    get_captured_log_content,
    get_captured_log_metadata,
    get_logs_captured_events,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.compute_log import (
        DgApiComputeLogLinkList,
        DgApiComputeLogList,
    )


@dataclass(frozen=True)
class DgApiComputeLogApi:
    """API for compute log operations."""

    client: IGraphQLClient

    def get_logs(
        self,
        run_id: str,
        step_key: str | None = None,
        cursor: str | None = None,
        max_bytes: int | None = None,
    ) -> "DgApiComputeLogList":
        """Get compute log content for a run.

        Two-phase approach: find LogsCapturedEvent entries, then fetch content per entry.
        """
        from dagster_dg_cli.api_layer.schemas.compute_log import (
            DgApiComputeLogList,
            DgApiStepComputeLog,
        )

        events = get_logs_captured_events(self.client, run_id, step_key=step_key)

        items: list[DgApiStepComputeLog] = []
        for event in events:
            file_key = event["fileKey"]
            log_key = [run_id, "compute_logs", file_key]
            content = get_captured_log_content(
                self.client, log_key, cursor=cursor, max_bytes=max_bytes
            )
            items.append(
                DgApiStepComputeLog(
                    file_key=file_key,
                    step_keys=event.get("stepKeys") or [],
                    stdout=content.get("stdout"),
                    stderr=content.get("stderr"),
                    cursor=content.get("cursor"),
                )
            )

        return DgApiComputeLogList(run_id=run_id, items=items, total=len(items))

    def get_log_links(
        self,
        run_id: str,
        step_key: str | None = None,
    ) -> "DgApiComputeLogLinkList":
        """Get compute log download URLs for a run.

        Two-phase approach: find LogsCapturedEvent entries, then fetch metadata per entry.
        """
        from dagster_dg_cli.api_layer.schemas.compute_log import (
            DgApiComputeLogLinkList,
            DgApiStepComputeLogLink,
        )

        events = get_logs_captured_events(self.client, run_id, step_key=step_key)

        items: list[DgApiStepComputeLogLink] = []
        for event in events:
            file_key = event["fileKey"]
            step_keys = event.get("stepKeys") or []

            # Check if external URLs are directly available from the event
            ext_stdout = event.get("externalStdoutUrl")
            ext_stderr = event.get("externalStderrUrl")

            if ext_stdout or ext_stderr:
                items.append(
                    DgApiStepComputeLogLink(
                        file_key=file_key,
                        step_keys=step_keys,
                        stdout_download_url=ext_stdout,
                        stderr_download_url=ext_stderr,
                    )
                )
            else:
                log_key = [run_id, "compute_logs", file_key]
                metadata = get_captured_log_metadata(self.client, log_key)
                items.append(
                    DgApiStepComputeLogLink(
                        file_key=file_key,
                        step_keys=step_keys,
                        stdout_download_url=metadata.get("stdoutDownloadUrl"),
                        stderr_download_url=metadata.get("stderrDownloadUrl"),
                    )
                )

        return DgApiComputeLogLinkList(run_id=run_id, items=items, total=len(items))
