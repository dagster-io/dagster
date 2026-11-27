"""Flows executed by a real Prefect worker in `test_message_readers.py`.

Live in their own module because a deployment names its flow by entrypoint, and the worker
imports this file in a fresh process.
"""

from dagster_pipes import PipesPrefectLogsMessageWriter, open_dagster_pipes
from prefect import flow, get_run_logger

PLAIN_LOG_LINE = "an ordinary Prefect log line"


@flow(name="reports-through-logs")
def reports_through_logs() -> None:
    get_run_logger().info(PLAIN_LOG_LINE)
    with open_dagster_pipes(message_writer=PipesPrefectLogsMessageWriter()) as pipes:
        pipes.report_asset_materialization(metadata={"rows": 100})


@flow(name="reports-too-much")
def reports_too_much() -> None:
    with open_dagster_pipes(message_writer=PipesPrefectLogsMessageWriter()) as pipes:
        pipes.report_asset_materialization(metadata={"blob": "x" * 1_000_000})


@flow(name="no-pipes")
def no_pipes() -> None:
    get_run_logger().info(PLAIN_LOG_LINE)
