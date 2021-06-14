import tempfile
from typing import List, Tuple
from unittest import mock

from dagster import SensorEvaluationContext
from dagster.core.instance.ref import InstanceRef
from hacker_news.sensors.hn_tables_updated_sensor import story_recommender_on_hn_table_update


def get_mock_events_for_asset_key(asset_events: List[Tuple[str, int]]):
    def events_for_asset_key(asset_key, after_cursor, **_kwargs):
        matching_events = [
            event
            for event in asset_events
            if asset_key.path[-1] == event[0] and (after_cursor is None or event[1] > after_cursor)
        ]
        return [(event[1], None) for event in matching_events]

    return events_for_asset_key


@mock.patch("dagster.core.instance.DagsterInstance.events_for_asset_key")
def test_first_events(mock_events_for_asset_key):
    mock_events_for_asset_key.side_effect = get_mock_events_for_asset_key(
        [("comments", 1), ("stories", 2)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key=None,
            last_completion_time=None,
            cursor=None,
        )
        requests = story_recommender_on_hn_table_update.evaluate_tick(context).run_requests
        assert len(requests) == 1
        assert requests[0].run_key == "1|2"


@mock.patch("dagster.core.instance.DagsterInstance.events_for_asset_key")
def test_nothing_new(mock_events_for_asset_key):
    mock_events_for_asset_key.side_effect = get_mock_events_for_asset_key(
        [("comments", 1), ("stories", 2)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
        )
        requests = story_recommender_on_hn_table_update.evaluate_tick(context).run_requests
        assert len(requests) == 0


@mock.patch("dagster.core.instance.DagsterInstance.events_for_asset_key")
def test_new_comments_old_stories(mock_events_for_asset_key):
    mock_events_for_asset_key.side_effect = get_mock_events_for_asset_key(
        [("comments", 1), ("comments", 2), ("stories", 2)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
        )
        requests = story_recommender_on_hn_table_update.evaluate_tick(context).run_requests
        assert len(requests) == 0


@mock.patch("dagster.core.instance.DagsterInstance.events_for_asset_key")
def test_old_comments_new_stories(mock_events_for_asset_key):
    mock_events_for_asset_key.side_effect = get_mock_events_for_asset_key(
        [("comments", 1), ("stories", 2), ("stories", 3)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:

        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
        )
        requests = story_recommender_on_hn_table_update.evaluate_tick(context).run_requests
        assert len(requests) == 0


@mock.patch("dagster.core.instance.DagsterInstance.events_for_asset_key")
def test_both_new(mock_events_for_asset_key):
    mock_events_for_asset_key.side_effect = get_mock_events_for_asset_key(
        [("comments", 1), ("comments", 2), ("stories", 2), ("stories", 3)]
    )

    with tempfile.TemporaryDirectory() as tmpdir_path:
        context = SensorEvaluationContext(
            instance_ref=InstanceRef.from_dir(tmpdir_path),
            last_run_key="1|2",
            last_completion_time=None,
            cursor=None,
        )
        requests = story_recommender_on_hn_table_update.evaluate_tick(context).run_requests
        assert len(requests) == 1
        assert requests[0].run_key == "2|3"
