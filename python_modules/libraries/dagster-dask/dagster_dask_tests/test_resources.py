from typing import Any, Mapping

from dagster import Dict, Output, op
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import execute_job
from dagster._core.execution.execution_result import ExecutionResult
from dagster._core.test_utils import instance_for_test
from dagster_dask import dask_resource
from dask.distributed import Client


@op(
    out={
        "scheduler_info": Out(Dict),
        "nthreads": Out(Dict),
    },
    required_resource_keys={"dask"},
)
def scheduler_info_op(context):
    with context.resources.dask.client.as_current():
        client = Client.current()

        yield Output(client.scheduler_info(), "scheduler_info")
        yield Output(client.nthreads(), "nthreads")


def scheduler_info_job() -> JobDefinition:
    @job(resource_defs={"dask": dask_resource})
    def job_def():
        scheduler_info_op()

    return job_def


def test_single_local_cluster():
    cluster_config = {
        "n_workers": 2,
        "threads_per_worker": 1,
        "dashboard_address": None,
    }
    with instance_for_test() as instance:
        run_config = {"resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}}
        with execute_job(
            reconstructable(scheduler_info_job),
            run_config=run_config,
            instance=instance,
        ) as result:
            _assert_scheduler_info_result(result, cluster_config)


def test_multiple_local_cluster():
    cluster_configs = [
        {
            "n_workers": 1,
            "threads_per_worker": 2,
            "dashboard_address": None,
        },
        {
            "n_workers": 2,
            "threads_per_worker": 1,
            "dashboard_address": None,
        },
    ]

    with instance_for_test() as instance:
        for cluster_config in cluster_configs:
            run_config = {"resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}}
            with execute_job(
                reconstructable(scheduler_info_job),
                run_config=run_config,
                instance=instance,
            ) as result:
                _assert_scheduler_info_result(result, cluster_config)


def _assert_scheduler_info_result(result: ExecutionResult, config: Mapping[str, Any]):
    scheduler_info = result.output_for_node("scheduler_info_op", "scheduler_info")
    assert isinstance(scheduler_info, dict)
    assert len(scheduler_info["workers"]) == config["n_workers"]

    nthreads = result.output_for_node("scheduler_info_op", "nthreads")
    assert isinstance(nthreads, dict)
    assert all(v == config["threads_per_worker"] for v in nthreads.values())
