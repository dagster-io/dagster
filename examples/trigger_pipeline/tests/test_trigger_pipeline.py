# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
import subprocess
import time
from contextlib import contextmanager

import requests
from dagster import execute_pipeline
from trigger_pipeline.trigger_pipeline.repo import do_math
from trigger_pipeline.trigger_pipeline.trigger import launch_pipeline_over_graphql

DAGIT_STARTUP_TIMEOUT = 15


def test_trigger_do_math_pipeline():
    run_config = {"solids": {"add_one": {"inputs": {"num": 5}}, "add_two": {"inputs": {"num": 6}}}}
    res = execute_pipeline(do_math, run_config=run_config)
    assert res.success
    assert res.result_for_solid("subtract").output_value() == -2


@contextmanager
def dagit_service_up():
    proc = subprocess.Popen(["dagit", "-f", "trigger_pipeline/repo.py"])
    try:
        yield proc
    finally:
        proc.kill()
        proc.wait()


def test_trigger_pipeline_by_gql():
    with dagit_service_up():
        start_time = time.time()
        dagit_host = "localhost"
        while True:
            if time.time() - start_time > DAGIT_STARTUP_TIMEOUT:
                raise Exception("Timed out waiting for dagit server to be available")

            try:
                sanity_check = requests.get(f"http://{dagit_host}:3000/dagit_info")
                assert "dagit" in sanity_check.text
                break
            except requests.exceptions.ConnectionError:
                pass

            time.sleep(1)

        REPOSITORY_LOCATION = "repo.py"
        REPOSITORY_NAME = "my_repo"
        PIPELINE_NAME = "do_math"
        RUN_CONFIG = {
            "solids": {"add_one": {"inputs": {"num": 5}}, "add_two": {"inputs": {"num": 6}}}
        }
        MODE = "default"
        result = launch_pipeline_over_graphql(
            location=REPOSITORY_LOCATION,
            repo_name=REPOSITORY_NAME,
            pipeline_name=PIPELINE_NAME,
            run_config=RUN_CONFIG,
            mode=MODE,
        )
        assert result["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
