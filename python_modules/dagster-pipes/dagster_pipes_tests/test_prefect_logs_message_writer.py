import json
import logging

import pytest
from dagster_pipes import DagsterPipesError, PipesPrefectLogsMessageWriter, _make_message

LOGGER_NAME = PipesPrefectLogsMessageWriter.LOGGER_NAME
PARAMS = {PipesPrefectLogsMessageWriter.PREFECT_LOGS_KEY: True}


def _written(caplog) -> list[dict]:
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == LOGGER_NAME]


def test_writes_one_info_record_per_message(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    with PipesPrefectLogsMessageWriter().open(PARAMS) as channel:
        channel.write_message(_make_message("opened", {"extras": {}}))
        channel.write_message(_make_message("closed", {}))

    assert [r.levelno for r in caplog.records] == [logging.INFO, logging.INFO]
    assert [m["method"] for m in _written(caplog)] == ["opened", "closed"]


def test_oversize_message_is_replaced_by_an_error_log(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    with PipesPrefectLogsMessageWriter().open(
        {
            **PARAMS,
            PipesPrefectLogsMessageWriter.MAX_MESSAGE_BYTES_KEY: 500,
        }
    ) as channel:
        channel.write_message(
            _make_message("report_asset_materialization", {"metadata": {"blob": "x" * 1_000}})
        )

    [message] = _written(caplog)
    assert message["method"] == "log"
    assert message["params"]["level"] == "ERROR"
    assert "`report_asset_materialization`" in message["params"]["message"]


def test_oversize_closed_message_still_closes(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    exception = {
        "message": "x" * 1_000,
        "stack": [],
        "name": "ValueError",
        "cause": None,
        "context": None,
    }
    with PipesPrefectLogsMessageWriter().open(
        {
            **PARAMS,
            PipesPrefectLogsMessageWriter.MAX_MESSAGE_BYTES_KEY: 500,
        }
    ) as channel:
        channel.write_message(_make_message("closed", {"exception": exception}))

    [message] = _written(caplog)
    assert message["method"] == "closed"
    assert message["params"]["exception"]["name"] == "ValueError"
    assert "Dropped a `closed` Pipes message" in message["params"]["exception"]["message"]


def test_requires_prefect_logs_param():
    with pytest.raises(DagsterPipesError, match="prefect_logs"):
        with PipesPrefectLogsMessageWriter().open({}):
            pass
