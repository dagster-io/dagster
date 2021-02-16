import sys
import zlib
from unittest import mock

from dagster import pipeline, solid
from dagster.core.storage.runs.sql_run_storage import defensively_unpack_pipeline_snapshot_query
from dagster.serdes import serialize_dagster_namedtuple


def test_defensive_pipeline_not_a_string():
    mock_logger = mock.MagicMock()

    assert defensively_unpack_pipeline_snapshot_query(mock_logger, [234]) is None
    assert mock_logger.warning.call_count == 1

    mock_logger.warning.assert_called_with(
        "get-pipeline-snapshot: First entry in row is not a binary type."
    )


def test_defensive_pipeline_not_bytes():
    mock_logger = mock.MagicMock()

    assert defensively_unpack_pipeline_snapshot_query(mock_logger, ["notbytes"]) is None
    assert mock_logger.warning.call_count == 1

    if sys.version_info.major == 2:
        # this error is not detected in python and instead fails on decompress
        # the joys of the python 2/3 unicode debacle
        mock_logger.warning.assert_called_with(
            "get-pipeline-snapshot: Could not decompress bytes stored in snapshot table."
        )
    else:
        mock_logger.warning.assert_called_with(
            "get-pipeline-snapshot: First entry in row is not a binary type."
        )


def test_defensive_pipelines_cannot_decompress():
    mock_logger = mock.MagicMock()

    assert defensively_unpack_pipeline_snapshot_query(mock_logger, [b"notbytes"]) is None
    assert mock_logger.warning.call_count == 1
    mock_logger.warning.assert_called_with(
        "get-pipeline-snapshot: Could not decompress bytes stored in snapshot table."
    )


def test_defensive_pipelines_cannot_decode_post_decompress():
    mock_logger = mock.MagicMock()

    # guarantee that we cannot decode by double compressing bytes.
    assert (
        defensively_unpack_pipeline_snapshot_query(
            mock_logger, [zlib.compress(zlib.compress(b"notbytes"))]
        )
        is None
    )
    assert mock_logger.warning.call_count == 1
    mock_logger.warning.assert_called_with(
        "get-pipeline-snapshot: Could not unicode decode decompressed bytes "
        "stored in snapshot table."
    )


def test_defensive_pipelines_cannot_parse_json():
    mock_logger = mock.MagicMock()

    assert (
        defensively_unpack_pipeline_snapshot_query(mock_logger, [zlib.compress(b"notjson")]) is None
    )
    assert mock_logger.warning.call_count == 1
    mock_logger.warning.assert_called_with(
        "get-pipeline-snapshot: Could not parse json in snapshot table."
    )


def test_correctly_fetch_decompress_parse_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    noop_pipeline_snapshot = noop_pipeline.get_pipeline_snapshot()

    mock_logger = mock.MagicMock()
    assert (
        defensively_unpack_pipeline_snapshot_query(
            mock_logger,
            [zlib.compress(serialize_dagster_namedtuple(noop_pipeline_snapshot).encode("utf-8"))],
        )
        == noop_pipeline_snapshot
    )

    assert mock_logger.warning.call_count == 0
