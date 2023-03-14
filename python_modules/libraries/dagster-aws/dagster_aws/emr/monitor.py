"""Monitoring for EMR on EKS job runs."""
import base64
import itertools
import json
import logging
import pickle
import sys
import time
from dataclasses import dataclass
from logging import Logger
from typing import Iterator, List

import boto3
from dagster.core.events import DagsterEvent

from .cloud_watch_logs_follower import CloudwatchLogsFollower

STATES_ONGOING = {"PENDING", "SUBMITTED", "RUNNING"}
STATES_SUCCESS = {"COMPLETED"}


def _is_final_event(event: DagsterEvent) -> bool:
    """Checks whether a Dagster event signals step success or failure"""
    return event.is_step_failure or event.is_step_success


@dataclass
class EmrEksJobError(Exception):
    """Error description for an EMR on EKS Job Run."""

    failure_reason: str
    state: str
    state_details: str


@dataclass
class EmrEksJobRunMonitor:
    """Monitor status and logs of an EMR on EKS Job Run.

    The status of the Job Run is periodically queried from
    the EMR on EKS API.

    In addition, the log streams for the Spark driver are
    tailed so that logs and events can be reported to Dagster.
    See ``EmrEksPySparkResource`` for details.
    """

    cluster_id: str
    region_name: str

    def __post_init__(self):
        self.emr_client = boto3.client("emr-containers", region_name=self.region_name)

    def consume_tailers(
        self,
        log: Logger,
        tailers: List[CloudwatchLogsFollower],
        log_stream_name_prefix: str,
    ) -> Iterator[DagsterEvent]:
        """Check logs from a list of log tailers. Yield events for logs corresponding to
        Dagster events, otherwise propagate the logs
        """
        # Get logs and events
        iterators = [tailer.fetch_events(log) for tailer in tailers]
        for log_record in itertools.chain(*iterators):
            msg = self._try_unpack_log_record(log_record["message"])

            # Remove the log stream name prefix: e.g.,
            # `some/prefix/stdout` -> `stdout`.
            log_stream = log_record["logStreamName"][len(log_stream_name_prefix) :]

            if self._is_dagster_event(msg):
                yield from self._yield_event(msg)
            else:
                self._write_log(log_stream, msg)

    def wait_for_completion(
        self,
        log: Logger,
        job_id: str,
        log_group_name: str,
        log_stream_name_prefix: str,
        start_timestamp_ms: int,
        wait_interval_secs: int = 10,
        max_wait_after_done_secs: int = 120,
    ) -> Iterator[DagsterEvent]:
        """Wait until the job finishes, and reports logs/events.

        Generic log events are written back to ``stdout`` or ``stderr``,
        which will be captured by Dagster directly.

        Log events containing a serialized Dagster event are yieled
        so that they can be reported to Dagster by the caller.
        """
        cw_client = boto3.client("logs", region_name=self.region_name)
        tailers = [
            CloudwatchLogsFollower(
                cw_client,
                log_group_name,
                log_stream_name_prefix + stream,
                start_timestamp_ms,
            )
            for stream in {"stdout", "stderr"}
        ]

        for tailer in tailers:
            log.info(f"Tailing logs in {tailer.log_group_name}/{tailer.log_stream_name_prefix}")

        done = False
        has_final_event = False
        while not done:
            time.sleep(wait_interval_secs)

            # Check Job Run status
            done = self._is_job_done(log, job_id)

            for event in self.consume_tailers(log, tailers, log_stream_name_prefix):
                if _is_final_event(event):
                    has_final_event = True
                yield event

        if has_final_event:
            return

        # Retry fetching the logs for some time until we have a final event
        for _ in range(int(max_wait_after_done_secs / wait_interval_secs)):
            time.sleep(wait_interval_secs)

            for event in self.consume_tailers(log, tailers, log_stream_name_prefix):
                yield event
                if _is_final_event(event):
                    return

    def _is_dagster_event(self, msg):
        # TODO: currently, serde logic for Dagster event is spread
        # between here and `job_main.py`. Move it to a single class
        # which can be used in both locations.

        return msg.startswith("""{"event":""")

    def _yield_event(self, msg: str) -> Iterator[DagsterEvent]:
        payload = json.loads(msg)
        event = pickle.loads(base64.b64decode(payload["event"].encode("ascii")))

        if not isinstance(event, DagsterEvent):
            raise RuntimeError(f"Event {event} was not a Dagster event")

        yield event

    def _write_log(self, log_stream: str, msg: str) -> None:
        if log_stream == "stdout":
            sys.stdout.write(msg + "\n")
        else:
            assert log_stream == "stderr"
            sys.stderr.write(msg + "\n")

    def _try_unpack_log_record(self, msg: str) -> str:
        # Messages are often JSON payloads themselves,
        # attempt to unwrap when possible.
        if msg.startswith("{"):
            try:
                msg_json = json.loads(msg)
                msg = msg_json.get("message", "")
            except ValueError:
                pass

        return msg

    def _is_job_done(self, log: logging.Logger, job_id: str) -> bool:
        response = self.emr_client.describe_job_run(id=job_id, virtualClusterId=self.cluster_id)
        job_run = response["jobRun"]

        log.info(f"Job is in state '{job_run['state']}'")

        if job_run["state"] in STATES_ONGOING:
            return False

        if job_run["state"] not in STATES_SUCCESS:
            raise EmrEksJobError(
                failure_reason=job_run["failureReason"],
                state=job_run["state"],
                state_details=job_run["stateDetails"],
            )

        return True
