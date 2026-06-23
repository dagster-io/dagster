from unittest import mock

import pytest
import requests
from dagster_airlift.core import AirflowBasicAuthBackend, AirflowInstance
from dagster_shared.error import DagsterError


def _response(status_code: int, body: dict | None = None, text: str = "") -> mock.Mock:
    resp = mock.Mock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    resp.json.return_value = body or {}
    return resp


def _instance_with_session(session: mock.Mock) -> AirflowInstance:
    auth = AirflowBasicAuthBackend(
        webserver_url="http://airflow.test", username="admin", password="admin"
    )
    auth.get_session = mock.Mock(return_value=session)  # ty: ignore[invalid-assignment]
    return AirflowInstance(auth_backend=auth, name="test")


def test_get_dag_run_retries_on_5xx_then_succeeds() -> None:
    """A transient 500 (e.g. Airflow SQLite-lock during basic-auth) is retried; the next 200 succeeds."""
    session = mock.Mock()
    session.get.side_effect = [
        _response(500, text="Ooops! database is locked"),
        _response(200, body={"state": "success"}),
    ]
    instance = _instance_with_session(session)
    with mock.patch("dagster_airlift.core.airflow_instance.time.sleep") as sleep_mock:
        dag_run = instance.get_dag_run(dag_id="dag", run_id="manual__2026-06-02")
    assert dag_run.run_id == "manual__2026-06-02"
    assert session.get.call_count == 2
    assert sleep_mock.call_count == 1


def test_get_dag_run_raises_after_exhausting_5xx_retries() -> None:
    """When every retry is also 5xx, the final 500 surfaces as DagsterError."""
    session = mock.Mock()
    session.get.return_value = _response(500, text="Ooops! database is locked")
    instance = _instance_with_session(session)
    with (
        mock.patch("dagster_airlift.core.airflow_instance.time.sleep"),
        pytest.raises(DagsterError, match=r"Status code: 500"),
    ):
        instance.get_dag_run(dag_id="dag", run_id="manual__2026-06-02")
    # retries=3 means 4 total attempts (initial + 3 retries)
    assert session.get.call_count == 4


def test_get_dag_run_does_not_retry_on_4xx() -> None:
    """4xx (e.g. nonexistent run) must surface immediately without retrying."""
    session = mock.Mock()
    session.get.return_value = _response(404, text="not found")
    instance = _instance_with_session(session)
    with pytest.raises(DagsterError, match=r"Status code: 404"):
        instance.get_dag_run(dag_id="dag", run_id="missing")
    assert session.get.call_count == 1
