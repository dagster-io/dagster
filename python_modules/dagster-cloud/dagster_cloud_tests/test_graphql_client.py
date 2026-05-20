import base64
import json
import platform
import re
import time
from contextlib import nullcontext
from email.utils import formatdate

import freezegun
import pytest
import responses
from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster._core.events.log import EventLogEntry
from dagster._core.test_utils import environ
from dagster_cloud.storage.client import DEFAULT_RETRIES
from dagster_cloud.version import __version__
from dagster_cloud_cli.core.errors import DagsterCloudAgentServerError
from dagster_cloud_cli.core.headers.impl import (
    API_TOKEN_HEADER,
    DAGSTER_CLOUD_VERSION_HEADER,
    PYTHON_VERSION_HEADER,
)
from requests.exceptions import ConnectionError as RequestsConnectionError

from dagster_cloud_tests import gen_agent_instance


@pytest.fixture(
    params=["graphql", "http"],
)
def api_protocol(request):
    with (
        environ({"DAGSTER_CLOUD_STORE_EVENT_OVER_HTTP": "1"})
        if request.param == "http"
        else nullcontext()
    ):
        yield request.param


@pytest.fixture
def graphql_url(dagster_cloud_url, api_protocol):
    if api_protocol == "graphql":
        return dagster_cloud_url + "/graphql"
    else:
        return dagster_cloud_url + "/store_events"


@pytest.fixture
def agent_instance(agent_token, dagster_cloud_url):
    with gen_agent_instance(dagster_cloud_url, agent_token) as instance:
        yield instance


@pytest.fixture
def proxy_graphql_client(agent_instance):
    return agent_instance.graphql_client


def test_graphql_client_headers(proxy_graphql_client, agent_token):
    headers = proxy_graphql_client.headers
    assert headers[DAGSTER_CLOUD_VERSION_HEADER] == __version__
    assert headers[PYTHON_VERSION_HEADER] == platform.python_version()
    assert headers[API_TOKEN_HEADER] == agent_token


@pytest.fixture
def fake_sleeps(monkeypatch):
    sleeps = []

    def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    yield sleeps


def create_test_event_log_record(message: str, run_id):
    return


def _store_event(agent_instance):
    event_log_entry = EventLogEntry(
        error_info=None,
        user_message="hello",
        level="debug",
        run_id="fake-run-id",
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ENGINE_EVENT.value,
            "nonce",
            event_specific_data=EngineEventData.in_process(999),
        ),
    )
    agent_instance.event_log_storage.store_event(event_log_entry)


@responses.activate
def test_graphql_client_backoff_succeeds(agent_instance, fake_sleeps, graphql_url):
    num_callbacks = {"num": 0}
    good_result = {"data": "youdidit"}

    def my_callback(request):
        num_callbacks["num"] = num_callbacks["num"] + 1
        if num_callbacks["num"] > 3:
            return (200, {}, json.dumps(good_result))

        return (502, {}, "")

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)

    _store_event(agent_instance)

    assert num_callbacks["num"] == 4
    assert fake_sleeps == [1, 2, 4]


@responses.activate
def test_graphql_client_429(agent_instance, fake_sleeps, graphql_url):
    num_callbacks = {"num": 0}
    good_result = {"data": "youdidit"}

    def my_callback(request):
        num_callbacks["num"] = num_callbacks["num"] + 1
        if num_callbacks["num"] > 3:
            return (200, {}, json.dumps(good_result))

        return (429, {"Retry-After": "10"}, "")

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)

    _store_event(agent_instance)

    assert num_callbacks["num"] == 4
    assert fake_sleeps == [10, 10, 10]


@responses.activate
def test_graphql_client_429_date(agent_instance, fake_sleeps, graphql_url):
    num_callbacks = {"num": 0}
    good_result = {"data": "youdidit"}

    with freezegun.freeze_time("2023-01-01"):
        now = time.time()
        future = now + 10

        def my_callback(request):
            num_callbacks["num"] = num_callbacks["num"] + 1
            if num_callbacks["num"] > 1:
                return (200, {}, json.dumps(good_result))

            return (429, {"Retry-After": formatdate(future, usegmt=True)}, "")

        responses.add_callback(responses.POST, graphql_url, callback=my_callback)

        _store_event(agent_instance)

        assert num_callbacks["num"] == 2
        assert fake_sleeps == [10]


@responses.activate
def test_graphql_client_429_bad_retry_after(agent_instance, fake_sleeps, graphql_url):
    num_callbacks = {"num": 0}
    good_result = {"data": "youdidit"}

    def my_callback(request):
        num_callbacks["num"] = num_callbacks["num"] + 1
        if num_callbacks["num"] > 3:
            return (200, {}, json.dumps(good_result))
        elif num_callbacks["num"] > 2:
            return (429, {"Retry-After": "junk"}, "")
        elif num_callbacks["num"] > 1:
            return (429, {"Retry-After": "-1"}, "")

        return (429, {}, "")

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)

    _store_event(agent_instance)

    assert num_callbacks["num"] == 4
    assert fake_sleeps == [1, 2, 4]


@responses.activate
def test_graphql_client_backoff_fails(agent_instance, fake_sleeps, graphql_url):
    num_callbacks = {"num": 0}

    def my_callback(request):
        num_callbacks["num"] = num_callbacks["num"] + 1
        return (502, {}, "")

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)

    with pytest.raises(
        DagsterCloudAgentServerError, match=re.escape("too many 502 error responses")
    ):
        _store_event(agent_instance)

    assert num_callbacks["num"] == DEFAULT_RETRIES + 1
    assert fake_sleeps == [1, 2, 4, 8, 16, 32]


@responses.activate
@pytest.mark.parametrize(
    "error_msg",
    [
        "SSLError",
        "ConnectTimeoutError",
        "Connection reset by peer",
    ],
)
def test_graphql_client_connection_retry_succeeds(
    agent_instance, fake_sleeps, error_msg, graphql_url
):
    num_callbacks = {"num": 0}
    good_result = {"data": "youdidit"}

    def my_callback(request):
        num_callbacks["num"] = num_callbacks["num"] + 1
        if num_callbacks["num"] > 5:
            return (200, {}, json.dumps(good_result))
        raise RequestsConnectionError(error_msg)

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)

    _store_event(agent_instance)

    assert num_callbacks["num"] == 6
    assert fake_sleeps == [1, 2, 4, 8, 16]


@responses.activate
def test_graphql_client_connection_reset_retry_fails(agent_instance, fake_sleeps, graphql_url):
    num_callbacks = {"num": 0}

    def my_callback(request):
        num_callbacks["num"] = num_callbacks["num"] + 1
        raise RequestsConnectionError("Connection reset by peer")

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)

    with pytest.raises(DagsterCloudAgentServerError, match=re.escape("Connection reset by peer")):
        _store_event(agent_instance)

    assert num_callbacks["num"] == DEFAULT_RETRIES + 1
    assert fake_sleeps == [1, 2, 4, 8, 16, 32]


@responses.activate
def test_graphql_client_metrics(agent_instance, fake_sleeps, graphql_url, monkeypatch):
    metric_headers = []

    def my_callback(request):
        metric_header = request.headers.get("Dagster-Cloud-Metric")
        if metric_header:
            metric_headers.append(json.loads(base64.b64decode(metric_header)))
        else:
            metric_headers.append(None)

        return (200, {}, json.dumps({"data": "good"}))

    responses.add_callback(responses.POST, graphql_url, callback=my_callback)
    monkeypatch.setenv("DISABLE_DAGSTER_CLOUD_STORE_EVENT_SEND_METRICS", "1")
    _store_event(agent_instance)
    monkeypatch.delenv("DISABLE_DAGSTER_CLOUD_STORE_EVENT_SEND_METRICS")
    _store_event(agent_instance)
    _store_event(agent_instance)
    monkeypatch.setenv("DISABLE_DAGSTER_CLOUD_STORE_EVENT_SEND_METRICS", "1")
    _store_event(agent_instance)

    assert metric_headers[0] is None
    assert metric_headers[1] is None, (
        "First event after we start recording will not have metric of previous event"
    )
    assert metric_headers[2], "expected metric of previous event"
    assert metric_headers[2]["_name"] == "store-event"
    assert metric_headers[2]["_duration"] > 0
    assert metric_headers[2]["event_type"] == "ENGINE_EVENT"
    assert metric_headers[2]["run_id"] == "fake-run-id"
    assert metric_headers[3] is None, "No metric sent after env turned off"
