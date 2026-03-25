from unittest.mock import MagicMock, patch

import dagster as dg
from project_dagster_modal_pipes.definitions import defs as _raw_defs

defs: dg.Definitions = _raw_defs() if not isinstance(_raw_defs, dg.Definitions) else _raw_defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)


def test_sensors_defined():
    repo = defs.get_repository_def()
    assert len(repo.sensor_defs) > 0


def test_assets_defined():
    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) > 0


def _get_sensor(name: str):
    repo = defs.get_repository_def()
    return next(s for s in repo.sensor_defs if s.name == name)


def _mock_feed_entry(entry_id: str, audio_url: str) -> MagicMock:
    """Build a mock feedparser entry with an audio link."""
    entry = MagicMock()
    entry.id = entry_id
    entry.links = [{"type": "audio/mpeg", "href": audio_url}]
    return entry


def test_rss_sensor_empty_feed_yields_no_run_requests():
    sensor = _get_sensor("rss_sensor_practical_ai")

    mock_feed = MagicMock()
    mock_feed.entries = []
    mock_feed.etag = "etag-v1"

    with patch(
        "project_dagster_modal_pipes.defs.pipeline_factory.feedparser.parse",
        return_value=mock_feed,
    ):
        context = dg.build_sensor_context()
        result = sensor(context)

    assert result.run_requests == []
    assert result.cursor == "etag-v1"


def test_rss_sensor_with_entries_creates_run_requests():
    sensor = _get_sensor("rss_sensor_practical_ai")

    entries = [
        _mock_feed_entry("https://example.com/ep1", "https://cdn.example.com/ep1.mp3"),
    ]

    mock_feed = MagicMock()
    mock_feed.entries = entries
    mock_feed.etag = "etag-v2"

    with patch(
        "project_dagster_modal_pipes.defs.pipeline_factory.feedparser.parse",
        return_value=mock_feed,
    ):
        context = dg.build_sensor_context()
        result = sensor(context)

    assert len(result.run_requests) == 1
    assert result.cursor == "etag-v2"


def test_rss_sensor_passes_etag_cursor_to_feedparser():
    sensor = _get_sensor("rss_sensor_comedy_bang_bang")

    mock_feed = MagicMock()
    mock_feed.entries = []
    mock_feed.etag = "new-etag"

    with patch(
        "project_dagster_modal_pipes.defs.pipeline_factory.feedparser.parse",
        return_value=mock_feed,
    ) as mock_parse:
        context = dg.build_sensor_context(cursor="prior-etag")
        sensor(context)

    _, call_kwargs = mock_parse.call_args
    assert call_kwargs.get("etag") == "prior-etag"


def test_rss_sensor_truncates_entries_to_max_backfill_size():
    """Sensor should not enqueue more than max_backfill_size entries."""
    sensor = _get_sensor("rss_sensor_practical_ai")

    entries = [
        _mock_feed_entry(f"https://example.com/ep{i}", f"https://cdn.example.com/ep{i}.mp3")
        for i in range(20)
    ]

    mock_feed = MagicMock()
    mock_feed.entries = entries
    mock_feed.etag = "etag-large"

    with patch(
        "project_dagster_modal_pipes.defs.pipeline_factory.feedparser.parse",
        return_value=mock_feed,
    ):
        context = dg.build_sensor_context()
        result = sensor(context)

    # RSSFeedDefinition.max_backfill_size defaults to 1
    assert len(result.run_requests) == 1
