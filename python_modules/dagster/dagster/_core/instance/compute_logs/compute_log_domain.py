"""Compute log domain for DagsterInstance."""

import logging
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from typing import IO, TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.storage.compute_log_manager import (
    CapturedLogContext,
    CapturedLogData,
    CapturedLogMetadata,
    CapturedLogSubscription,
    ComputeIOType,
)

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance

logger = logging.getLogger(__name__)


class ComputeLogDomain:
    """Domain object encapsulating compute log operations.

    This class holds a reference to a DagsterInstance and provides methods
    for capturing, retrieving, and managing compute logs for steps.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Generator[CapturedLogContext, None, None]:
        """Context manager for capturing the stdout/stderr within the current process.

        Args:
            log_key: The log key identifying the captured logs

        Yields:
            CapturedLogContext: Context object containing log key and external URL info
        """
        check.sequence_param(log_key, "log_key", of_type=str)
        logger.debug(f"Starting log capture for key: {log_key}")

        with self._instance.compute_log_manager.capture_logs(log_key) as context:
            logger.debug(f"Log capture active for key: {log_key}")
            yield context

        logger.debug(f"Log capture completed for key: {log_key}")

    @contextmanager
    def open_log_stream(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Iterator[Optional[IO[bytes]]]:
        """Context manager for providing an IO stream for writing logs.

        Args:
            log_key: The log key identifying the captured logs
            io_type: Whether to write to stdout or stderr stream

        Yields:
            Optional IO stream for writing log bytes
        """
        check.sequence_param(log_key, "log_key", of_type=str)
        check.inst_param(io_type, "io_type", ComputeIOType)

        logger.debug(f"Opening {io_type.value} log stream for key: {log_key}")

        with self._instance.compute_log_manager.open_log_stream(log_key, io_type) as stream:
            yield stream

    def is_capture_complete(self, log_key: Sequence[str]) -> bool:
        """Check if log capture for the given log key has completed.

        Args:
            log_key: The log key identifying the captured logs

        Returns:
            True if capture is complete, False otherwise
        """
        check.sequence_param(log_key, "log_key", of_type=str)
        return self._instance.compute_log_manager.is_capture_complete(log_key)

    def get_log_data(
        self,
        log_key: Sequence[str],
        cursor: Optional[str] = None,
        max_bytes: Optional[int] = None,
    ) -> CapturedLogData:
        """Get captured log data for the given log key.

        This is the most commonly used method for retrieving compute logs.
        Includes additional error handling and logging.

        Args:
            log_key: The log key identifying the captured logs
            cursor: Optional cursor for pagination through log data
            max_bytes: Optional limit on the size of data to retrieve

        Returns:
            CapturedLogData containing log bytes and cursor information
        """
        check.sequence_param(log_key, "log_key", of_type=str)
        check.opt_str_param(cursor, "cursor")
        check.opt_int_param(max_bytes, "max_bytes")

        try:
            log_data = self._instance.compute_log_manager.get_log_data(log_key, cursor, max_bytes)
            logger.debug(f"Retrieved log data for key: {log_key}, cursor: {cursor}")
            return log_data
        except Exception as e:
            logger.warning(f"Failed to retrieve log data for key {log_key}: {e}")
            raise

    def get_log_metadata(self, log_key: Sequence[str]) -> CapturedLogMetadata:
        """Get metadata for captured logs including external URLs and file paths.

        Args:
            log_key: The log key identifying the captured logs

        Returns:
            CapturedLogMetadata with display information about log storage
        """
        check.sequence_param(log_key, "log_key", of_type=str)
        return self._instance.compute_log_manager.get_log_metadata(log_key)

    def delete_logs(
        self,
        log_key: Optional[Sequence[str]] = None,
        prefix: Optional[Sequence[str]] = None,
    ) -> None:
        """Delete captured logs for the given log key or prefix.

        Args:
            log_key: Specific log key to delete (mutually exclusive with prefix)
            prefix: Prefix of log keys to delete (mutually exclusive with log_key)
        """
        if log_key is not None and prefix is not None:
            check.failed("Cannot specify both log_key and prefix")
        if log_key is None and prefix is None:
            check.failed("Must specify either log_key or prefix")

        if log_key is not None:
            check.sequence_param(log_key, "log_key", of_type=str)
            logger.debug(f"Deleting logs for key: {log_key}")
        else:
            check.sequence_param(prefix, "prefix", of_type=str)
            logger.debug(f"Deleting logs with prefix: {prefix}")

        self._instance.compute_log_manager.delete_logs(log_key=log_key, prefix=prefix)

    def subscribe(
        self, log_key: Sequence[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        """Subscribe to log updates for real-time log streaming.

        Args:
            log_key: The log key identifying the captured logs
            cursor: Optional cursor position to start streaming from

        Returns:
            CapturedLogSubscription for receiving log updates
        """
        check.sequence_param(log_key, "log_key", of_type=str)
        check.opt_str_param(cursor, "cursor")

        logger.debug(f"Creating log subscription for key: {log_key}, cursor: {cursor}")
        return self._instance.compute_log_manager.subscribe(log_key, cursor)

    def unsubscribe(self, subscription: CapturedLogSubscription) -> None:
        """Unsubscribe from log updates.

        Args:
            subscription: The subscription object to cancel
        """
        check.inst_param(subscription, "subscription", CapturedLogSubscription)
        logger.debug(f"Cancelling log subscription for key: {subscription.log_key}")
        self._instance.compute_log_manager.unsubscribe(subscription)

    def build_log_key_for_run(self, run_id: str, step_key: str) -> Sequence[str]:
        """Build a log key for a specific run and step.

        Args:
            run_id: The run ID
            step_key: The step key within the run

        Returns:
            Log key sequence identifying this run/step combination
        """
        check.str_param(run_id, "run_id")
        check.str_param(step_key, "step_key")

        # Most compute log managers use [run_id, step_key] as the log key format
        return [run_id, step_key]

    # Convenience methods that combine multiple operations

    def get_logs_for_run(
        self, run_id: str, step_key: str, cursor: Optional[str] = None
    ) -> CapturedLogData:
        """Convenience method to get logs for a specific run and step.

        Args:
            run_id: The run ID
            step_key: The step key within the run
            cursor: Optional cursor for pagination

        Returns:
            CapturedLogData for the specified run and step
        """
        log_key = self.build_log_key_for_run(run_id, step_key)
        return self.get_log_data(log_key, cursor=cursor)

    def cleanup_logs_for_run(self, run_id: str) -> None:
        """Delete all compute logs for a specific run.

        Args:
            run_id: The run ID to clean up logs for
        """
        check.str_param(run_id, "run_id")
        logger.info(f"Cleaning up compute logs for run: {run_id}")

        # Delete using run_id as prefix to remove all steps for this run
        self.delete_logs(prefix=[run_id])

    def get_log_summary(self, log_key: Sequence[str]) -> dict:
        """Get summary information about captured logs.

        Args:
            log_key: The log key identifying the captured logs

        Returns:
            Dictionary containing log summary information
        """
        check.sequence_param(log_key, "log_key", of_type=str)

        metadata = self.get_log_metadata(log_key)
        is_complete = self.is_capture_complete(log_key)

        return {
            "log_key": log_key,
            "is_capture_complete": is_complete,
            "stdout_location": metadata.stdout_location,
            "stderr_location": metadata.stderr_location,
            "stdout_download_url": metadata.stdout_download_url,
            "stderr_download_url": metadata.stderr_download_url,
        }
