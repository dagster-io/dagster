"""Example Dagster job mimicing some Data Pipeline structure.
​
TODO: https://docs.dagster.io/guides/dagster/graph_job_op
​
Following https://docs.dagster.io/tutorial .
​
Run on the CLI:
    dagster job execute -f main.py -c run_config.yaml
Run with UI:
    dagit -f main.py  # and copy run_config.yaml into the UI
When running with the UI, simply save changes to this file and then "Re-execute All".
"""
import enum
import random
import time
from typing import Dict, List
import pandas as pd
from dagster import DynamicOut
from dagster import DynamicOutput
from dagster import ModeDefinition
from dagster import Nothing
from dagster import Optional
from dagster import Out
from dagster import Output
from dagster import ScheduleDefinition
from dagster import fs_io_manager
from dagster import job
from dagster import op
from dagster import repository
from dagster_k8s import k8s_job_executor
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource
from .test_step_delegating_executor import test_step_delegating_executor


class _Cycler(enum.Enum):
    MACCOR = enum.auto()
    ARBIN4 = enum.auto()
    ARBIN8 = enum.auto()


class _Test:
    """Container class for information about a test."""

    def __init__(self, test_id):
        self.test_id = test_id
        self.cycler = None


@op(
    config_schema={"test_ids": list},
)
def determine_test_ids_to_process(context) -> List[str]:
    """Reads a list of test IDs to process from the run configuration.
    ​
        https://docs.dagster.io/concepts/configuration/config-schema
    """
    test_ids = context.op_config["test_ids"]
    context.log.info(f"Will process {len(test_ids)} tests.")
    return test_ids


@op
def build_test_to_cycler_map(context, test_ids: List[str]) -> Dict[str, _Cycler]:
    test_to_cycler_map = {}
    for test_id in test_ids:
        # if random.random() < 0.3:  # Simulate a moderate error rate.
        if test_id == "10010":  # force skipping only one of the nodes to trigger an error
            continue
        test_to_cycler_map[test_id] = random.choice(list(_Cycler))
    return test_to_cycler_map


@op(
    out=DynamicOut(_Test),
)
def assign_cycler_and_shard(
    context, test_ids: List[str], test_to_cycler_map: Dict[str, _Cycler]
) -> _Test:
    """Maps tests to cyclers, and then yields outputs which will be used in parallel.
    ​
        Dynamic outputs: https://docs.dagster.io/concepts/ops-jobs/jobs#dynamic-mapping--collect
    """
    for test in map(_Test, test_ids):
        time.sleep(random.random())
        try:
            test.cycler = test_to_cycler_map[test.test_id]
        except KeyError:
            context.log.error(f"No cycler has data for {test.test_id}")
            # Picked up as a missing dict entry and raised below.
            # https://docs.dagster.io/concepts/ops-jobs/op-events
        yield DynamicOutput(value=test, mapping_key=test.test_id)


@op(out=Out(_Test, "test_with_data", is_required=False))
def read_test_data(context, test: _Test) -> _Test:
    """Optionally outputs test data from a cycler.
    ​
        If we can't read the test's data for some reason, skip the rest of the DAG for that test.
        https://stackoverflow.com/questions/62025039/how-to-avoid-running-the-rest-of-a-dagster-job-under-certain-conditions
    """
    try:
        test_with_data = {
            _Cycler.MACCOR: _read_maccor_test_data,
            _Cycler.ARBIN4: _read_arbin4_test_data,
            _Cycler.ARBIN8: _read_arbin8_test_data,
        }[test.cycler](context, test)
        yield Output(test_with_data)
    except KeyError:
        context.log.error(f"Test {test.test_id} cannot fetch data from cycler {test.cycler}.")


def _read_maccor_test_data(context, test: _Test) -> _Test:
    """Regular Python function to simulate a MaccorInputManager or similar."""
    test.df = pd.DataFrame(
        {
            "time": [13000, 13001, 13002, 13003],
            "voltage": [random.random()] * 4,
        }
    )
    time.sleep(random.randint(2, 5))
    return test


def _read_arbin4_test_data(context, test: _Test) -> _Test:
    test.df = pd.DataFrame(
        {
            "time": [4000, 4001, 4002, 4003],
            "Vmax": [random.random()] * 4,
        }
    )
    time.sleep(random.randint(2, 5))
    return test


def _read_arbin8_test_data(context, test: _Test) -> _Test:
    test.df = pd.DataFrame(
        {
            "time": [8000, 8001, 8002, 8003],
            "v": [random.random()] * 4,
        }
    )
    time.sleep(random.randint(2, 5))
    return test


@op
def write_test_data(context, test: _Test) -> bool:
    time.sleep(random.randint(1, 3))
    # Return some value for DAG construction only, so Dagster the main job
    # function can link outputs from this to inputs of other ops.
    return True


@op
def summarize(context, test_ids: List[str], successes: List[bool]) -> Nothing:
    context.log.info(f"Pipeline complete, {len(successes)} of {len(test_ids)} tests processed.")


def get_dynamic_job():
    @job(
        # Use the filesystem to store serialized IOs.
        # https://docs.dagster.io/concepts/io-management/io-managers
        executor_def=test_step_delegating_executor,
    )
    def battery_data_job():
        """The main job definition, which connects inputs/outputs of the ops (nodes)."""
        test_ids = determine_test_ids_to_process()
        test_to_cycler_map = build_test_to_cycler_map(test_ids)
        tests_with_cycler = assign_cycler_and_shard(test_ids, test_to_cycler_map)
        tests_with_data = tests_with_cycler.map(read_test_data)
        sync = tests_with_data.map(write_test_data).collect()
        summarize(test_ids, sync)

    return battery_data_job
