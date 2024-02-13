import json
from typing import List, Tuple
from unittest import mock

from dagster import EventLogRecord, GraphDefinition, build_sensor_context
from dagster._core.test_utils import instance_for_test

from project_fully_featured.sensors.hn_tables_updated_sensor import (
    make_hn_tables_updated_sensor,
)


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


@mock.patch("dagster._core.instance.DagsterInstance.get_event_records")
def test_first_events(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records([("comments", 1), ("stories", 2)])

    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance)
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 1
        assert result.cursor == json.dumps({"comments": 1, "stories": 2})


@mock.patch("dagster._core.instance.DagsterInstance.get_event_records")
def test_nothing_new(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records([("comments", 1), ("stories", 2)])

    with instance_for_test() as instance:
        context = build_sensor_context(
            instance=instance, cursor=json.dumps({"comments": 1, "stories": 2})
        )
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 0
        assert result.cursor == json.dumps({"comments": 1, "stories": 2})


@mock.patch("dagster._core.instance.DagsterInstance.get_event_records")
def test_new_comments_old_stories(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records(
        [("comments", 1), ("comments", 2), ("stories", 2)]
    )

    with instance_for_test() as instance:
        context = build_sensor_context(
            instance=instance, cursor=json.dumps({"comments": 1, "stories": 2})
        )
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 0


@mock.patch("dagster._core.instance.DagsterInstance.get_event_records")
def test_old_comments_new_stories(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records(
        [("comments", 1), ("stories", 2), ("stories", 3)]
    )

    with instance_for_test() as instance:
        context = build_sensor_context(
            instance=instance, cursor=json.dumps({"comments": 1, "stories": 2})
        )
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 0


@mock.patch("dagster._core.instance.DagsterInstance.get_event_records")
def test_both_new(mock_event_records):
    mock_event_records.side_effect = get_mock_event_records(
        [("comments", 1), ("comments", 2), ("stories", 2), ("stories", 3)]
    )

    with instance_for_test() as instance:
        context = build_sensor_context(
            instance=instance, cursor=json.dumps({"comments": 1, "stories": 2})
        )
        result = make_hn_tables_updated_sensor(job=GraphDefinition("test")).evaluate_tick(context)
        assert len(result.run_requests) == 1
        assert result.cursor == json.dumps({"comments": 2, "stories": 3})
