from collections import defaultdict
from typing import DefaultDict

import botocore


class CloudwatchLogsFollower:
    """Tail CloudWatch Logs from log streams.

    CloudWatch Logs has no API to directly stream new log
    events from log streams. Instead, we have to regularly
    fetch new logs using an appropriate ``startTime`` argument.

    Multiple log streams
    --------------------
    When ``log_stream_name_prefix`` matches multiple log streams,
    it is possible that some log events will be missed.

    Assuming two log streams ``A`` and ``B``, ``filter_log_events``
    might returns log events for ``B`` if those are available. In
    our next call to ``filter_log_events``, only events with a
    larger timestamp will be queried. However, if events for ``A``
    with an earlier timestamp are pushed to CloudWatch afterwards,
    these will never be queried.

    We could improve this class to handle such cases by querying
    each log stream in isolation, although that can be much less
    efficient if there are many log streams matching the prefix.
    If you need this to be reliable and have only a few log streams,
    consider instantiating one follower per log stream instead of
    relying on a single follower and the prefix.
    """

    def __init__(
        self,
        client: "botocore.client.logs",
        log_group_name: str,
        log_stream_name_prefix: str,
        start_timestamp_ms: int,
    ) -> None:
        self._client = client
        self._max_timestamp = start_timestamp_ms
        self._ts_to_event_ids: DefaultDict = defaultdict(set)

        self.log_group_name = log_group_name
        self.log_stream_name_prefix = log_stream_name_prefix

    def fetch_events(self, log):
        """Fetch new events from the log streams."""
        next_token = None

        while True:
            if next_token:
                paging_args = {"nextToken": next_token}
            else:
                paging_args = {"startTime": self._max_timestamp}

            log.debug(
                f"Fetching log events for logGroupName={self.log_group_name}, "
                f"logStreamNamePrefix={self.log_stream_name_prefix}, "
                f"with args: {paging_args}"
            )

            response = self._client.filter_log_events(
                logGroupName=self.log_group_name,
                logStreamNamePrefix=self.log_stream_name_prefix,
                **paging_args,
            )

            for event in response["events"]:
                # After we have queried all the pages, we will resume
                # polling with the maximum timestamp seen so far.
                #
                # To avoid seeing previous events multiple times, we
                # keep track of past event IDs.
                if event["eventId"] not in self._ts_to_event_ids[event["timestamp"]]:
                    self._ts_to_event_ids[event["timestamp"]].add(event["eventId"])
                    yield event

            if self._ts_to_event_ids:
                # Discard event IDs for previous timestamps
                self._max_timestamp = max(self._ts_to_event_ids)
                events = self._ts_to_event_ids[self._max_timestamp]

                self._ts_to_event_ids = defaultdict(set, {self._max_timestamp: events})

            next_token = response.get("nextToken")

            if not next_token:
                break  # No more pages to fetch
