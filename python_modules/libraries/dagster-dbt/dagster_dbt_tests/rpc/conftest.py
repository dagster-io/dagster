import atexit
import json
import subprocess
import time
from urllib import request
from urllib.error import URLError

import pytest
import responses
from dagster_dbt import DbtRpcClient

TEST_HOSTNAME = "127.0.0.1"
TEST_PORT = 8580
RPC_ESTABLISH_RETRIES = 4
RPC_ESTABLISH_RETRY_INTERVAL_S = 1.5

RPC_ENDPOINT = "http://{hostname}:{port}/jsonrpc".format(hostname=TEST_HOSTNAME, port=TEST_PORT)

# ======= SOLIDS I ========


def get_rpc_server_status():
    status_request_body = b'{"jsonrpc": "2.0", "method": "status", "id": 1}'
    req = request.Request(
        RPC_ENDPOINT,
        data=status_request_body,
        headers={"Content-type": "application/json"},
    )
    resp = request.urlopen(req)
    return json.load(resp)


all_subprocs = set()


def kill_all_subprocs():
    for proc in all_subprocs:
        proc.kill()


atexit.register(kill_all_subprocs)


@pytest.fixture(scope="class")
def dbt_rpc_server(
    dbt_seed, dbt_executable, dbt_config_dir
):  # pylint: disable=unused-argument, redefined-outer-name
    proc = subprocess.Popen(
        [
            dbt_executable,
            "rpc",
            "--host",
            TEST_HOSTNAME,
            "--port",
            str(TEST_PORT),
            "--profiles-dir",
            dbt_config_dir,
        ],
    )

    # schedule to be killed in case of abort
    all_subprocs.add(proc)

    tries_remaining = RPC_ESTABLISH_RETRIES
    while True:
        poll_result = proc.poll()  # check on the child
        if poll_result != None:
            raise Exception("DBT subprocess terminated before test could start.")

        try:
            status_json = get_rpc_server_status()
            if status_json["result"]["state"] == "ready":
                break
        except URLError:
            pass

        if tries_remaining <= 0:
            raise Exception("Exceeded max tries waiting for DBT RPC server to be ready.")
        tries_remaining -= 1
        time.sleep(RPC_ESTABLISH_RETRY_INTERVAL_S)

    yield

    proc.terminate()  # clean up after ourself
    proc.wait(timeout=0.2)
    if proc.poll() == None:  # still running
        proc.kill()
    all_subprocs.remove(proc)


# ======= SOLIDS II ========
@pytest.fixture(scope="session")
def rpc_endpoint():
    return RPC_ENDPOINT


@pytest.fixture
def rsps():
    with responses.RequestsMock() as req_mock:
        yield req_mock


@pytest.fixture
def non_terminal_poll_result(rpc_logs):  # pylint: disable=redefined-outer-name
    result = {
        "result": {
            "state": "running",
            "start": "2020-03-10T17:49:39.095678Z",
            "end": None,
            "elapsed": 1.471953,
            "logs": rpc_logs,
            "tags": {},
        },
        "id": "846157fe-62f7-11ea-9cd7-acde48001122",
        "jsonrpc": "2.0",
    }
    return result


@pytest.fixture
def terminal_poll_result(rpc_logs):  # pylint: disable=redefined-outer-name
    result = {
        "result": {
            "state": "success",
            "start": "2020-03-10T17:52:19.254197Z",
            "end": "2020-03-10T17:53:06.195224Z",
            "elapsed": 46.941027,
            "logs": rpc_logs,
            "tags": {},
            "results": [
                {
                    "node": {
                        "raw_sql": "\n\n{{\n  config(\n    unique_key='ds',\n    strategy='check',\n    check_cols='all'\n  )\n}}\n\nselect src.*\nfrom {{ source('dagster', 'daily_fulfillment_forecast') }} src\n\n",
                        "database": "snapshots_david_wallace",
                        "schema": "dagster",
                        "fqn": [
                            "dataland_dbt",
                            "dagster",
                            "daily_fulfillment_forecast_snapshot",
                            "daily_fulfillment_forecast_snapshot",
                        ],
                        "unique_id": "snapshot.dataland_dbt.daily_fulfillment_forecast_snapshot",
                        "package_name": "dataland_dbt",
                        "root_path": "/Users/dwall/repos/dataland-dbt",
                        "path": "dagster/daily_fulfillment_forecast_snapshot.sql",
                        "original_file_path": "snapshots/dagster/daily_fulfillment_forecast_snapshot.sql",
                        "name": "daily_fulfillment_forecast_snapshot",
                        "resource_type": "snapshot",
                        "alias": "daily_fulfillment_forecast_snapshot",
                        "config": {
                            "enabled": True,
                            "materialized": "snapshot",
                            "persist_docs": {},
                            "post-hook": [],
                            "pre-hook": [],
                            "vars": {},
                            "quoting": {},
                            "column_types": {},
                            "tags": [],
                            "unique_key": "ds",
                            "target_schema": "dagster",
                            "target_database": "snapshots_david_wallace",
                            "strategy": "check",
                            "check_cols": "all",
                            "transient": False,
                        },
                        "tags": [],
                        "refs": [],
                        "sources": [["dagster", "daily_fulfillment_forecast"]],
                        "depends_on": {
                            "nodes": ["source.dataland_dbt.dagster.daily_fulfillment_forecast"],
                            "macros": [],
                        },
                        "docrefs": [],
                        "description": "",
                        "columns": {},
                        "patch_path": None,
                        "build_path": "target/run/dataland_dbt/dagster/daily_fulfillment_forecast_snapshot.sql",
                        "compiled": True,
                        "compiled_sql": "\n\n\n\nselect src.*\nfrom ingest_dev.dagster.daily_fulfillment_forecast src\n",
                        "extra_ctes_injected": True,
                        "extra_ctes": [],
                        "injected_sql": "\n\n\n\nselect src.*\nfrom ingest_dev.dagster.daily_fulfillment_forecast src\n",
                        "wrapped_sql": "None",
                    },
                    "error": None,
                    "status": "SUCCESS 0",
                    "execution_time": 14.527844190597534,
                    "thread_id": "Thread-1",
                    "timing": [
                        {
                            "name": "compile",
                            "started_at": "2020-03-10T17:52:50.519541Z",
                            "completed_at": "2020-03-10T17:52:50.533709Z",
                        },
                        {
                            "name": "execute",
                            "started_at": "2020-03-10T17:52:50.533986Z",
                            "completed_at": "2020-03-10T17:53:05.046646Z",
                        },
                    ],
                    "fail": None,
                    "warn": None,
                    "skip": False,
                }
            ],
            "generated_at": "2020-03-10T17:53:06.001341Z",
            "elapsed_time": 44.305715799331665,
        },
        "id": "016d2822-62f8-11ea-906b-acde48001122",
        "jsonrpc": "2.0",
    }
    return result


# ======= CLIENT ========
@pytest.fixture(scope="session")
def client():
    return DbtRpcClient(host="0.0.0.0", port=8580)


# ======= UTILS ========
@pytest.fixture
def rpc_logs():
    return [
        {
            "timestamp": "2020-03-10T18:19:06.726848Z",
            "message": "finished collecting timing info",
            "channel": "dbt",
            "level": 10,
            "levelname": "DEBUG",
            "thread_name": "Thread-1",
            "process": 18546,
            "extra": {
                "timing_info": {
                    "name": "execute",
                    "started_at": "2020-03-10T18:18:54.823894Z",
                    "completed_at": "2020-03-10T18:19:06.726805Z",
                },
                "json_only": True,
                "unique_id": "snapshot.dataland_dbt.daily_fulfillment_forecast_snapshot",
                "run_state": "running",
                "context": "server",
            },
            "exc_info": None,
        },
        {
            "timestamp": "2020-03-10T18:19:06.727723Z",
            "message": "11:19:06 | 1 of 1 OK snapshotted snapshots_david_wallace.dagster.daily_fulfillment_forecast_snapshot [\u001b[32mSUCCESS 0\u001b[0m in 11.92s]",
            "channel": "dbt",
            "level": 11,
            "levelname": "INFO",
            "thread_name": "Thread-1",
            "process": 18546,
            "extra": {
                "unique_id": "snapshot.dataland_dbt.daily_fulfillment_forecast_snapshot",
                "run_state": "running",
                "context": "server",
            },
            "exc_info": None,
        },
    ]
