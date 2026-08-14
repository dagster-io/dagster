"""index_refresh_sensor cursor-behavior tests (Step 12)."""

from dagster import RunRequest, SkipReason, build_sensor_context
from ragas_evaluation_pipeline.config import INDEX_VERSION_PATH
from ragas_evaluation_pipeline.sensors import index_refresh_sensor

_CURRENT = INDEX_VERSION_PATH.read_text(encoding="utf-8").strip()


def test_sensor_fires_when_no_cursor():
    result = index_refresh_sensor(build_sensor_context())
    assert isinstance(result, RunRequest)
    assert result.run_key == _CURRENT


def test_sensor_skips_when_cursor_matches_current_index():
    result = index_refresh_sensor(build_sensor_context(cursor=_CURRENT))
    assert isinstance(result, SkipReason)


def test_sensor_fires_when_cursor_is_stale():
    result = index_refresh_sensor(build_sensor_context(cursor="idx-OUTDATED"))
    assert isinstance(result, RunRequest)
    assert result.run_key == _CURRENT
