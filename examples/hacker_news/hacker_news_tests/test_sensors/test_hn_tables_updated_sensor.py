import tempfile
from typing import List, Tuple
from unittest import mock

from dagster import SensorEvaluationContext
from dagster.core.instance.ref import InstanceRef
from dagster.core.storage.event_log.base import EventLogRecord
from hacker_news.sensors.hn_tables_updated_sensor import story_recommender_on_hn_table_update_prod


def get_mock_event_records(asset_events: List[Tuple[str, int]]):
    def event_records(event_records_filter, **_kwargs):
        asset_key = event_records_filter.asset_key
        after_cursor = event_records_filter.after_cursor
        matching_events = [
            event
            for event in asset_events
            if asset_key.path[-1] == event[0] and (after_cursor is None or event[1] > after_cursor)
        ]
        return [
            EventLogRecord(storage_id=event[1], event_log_entry=None) for event in matching_events
        ]

    return event_records


@mock.patch("dagster.core.instance.DagsterInstance.get_event_records")
def test_first_events(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records([("comments", 1), ("stories", 2)])

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key=None,
            last_completion_time=None,
            cursor=None,
            repository_name=None,
        )
        requests = story_recommender_on_hn_table_update_prod.evaluate_tick(context).run_requests
        assert len(requests) == 1
        assert requests[0].run_key == "1|2"


@mock.patch("dagster.core.instance.DagsterInstance.get_event_records")
def test_nothing_new(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records([("comments", 1), ("stories", 2)])

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
            repository_name=None,
        )
        requests = story_recommender_on_hn_table_update_prod.evaluate_tick(context).run_requests
        assert len(requests) == 0


@mock.patch("dagster.core.instance.DagsterInstance.get_event_records")
def test_new_comments_old_stories(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records(
        [("comments", 1), ("comments", 2), ("stories", 2)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
            repository_name=None,
        )
        requests = story_recommender_on_hn_table_update_prod.evaluate_tick(context).run_requests
        assert len(requests) == 0


@mock.patch("dagster.core.instance.DagsterInstance.get_event_records")
def test_old_comments_new_stories(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records(
        [("comments", 1), ("stories", 2), ("stories", 3)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:

        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
            repository_name=None,
        )
        requests = story_recommender_on_hn_table_update_prod.evaluate_tick(context).run_requests
        assert len(requests) == 0


@mock.patch("dagster.core.instance.DagsterInstance.get_event_records")
def test_both_new(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records(
        [("comments", 1), ("comments", 2), ("stories", 2), ("stories", 3)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
            repository_name=None,
        )
        requests = story_recommender_on_hn_table_update_prod.evaluate_tick(context).run_requests
        assert len(requests) == 1
        assert requests[0].run_key == "2|3"
