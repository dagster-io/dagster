import os
import re
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, Iterator, Optional

import dagster._check as check
import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterPipesExecutionError
from dagster_databricks._test_utils import (
    databricks_client,  # noqa: F401
    temp_dbfs_script,
    upload_dagster_pipes_whl,
)
from dagster_databricks.pipes import PipesDatabricksClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import compute, jobs

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def script_fn():
    import os
    import sys

    from dagster_pipes import (
        DAGSTER_PIPES_CONTEXT_ENV_VAR,
        PipesCliArgsParamsLoader,
        PipesDbfsContextLoader,
        PipesDbfsMessageWriter,
        PipesEnvVarParamsLoader,
        open_dagster_pipes,
    )

    # To facilitate using the same script for testing in both the new cluster and existing cluster
    # instances, , we dynamically configure the PipesParamsLoader here by checking for the presence
    # of pipes-specific env vars. If these are set, we know we are in the new cluster case and load
    # params via the env vars.
    params_loader = (
        PipesEnvVarParamsLoader()
        if DAGSTER_PIPES_CONTEXT_ENV_VAR in os.environ
        else PipesCliArgsParamsLoader()
    )

    with open_dagster_pipes(
        params_loader=params_loader,
        context_loader=PipesDbfsContextLoader(),
        message_writer=PipesDbfsMessageWriter(),
    ) as context:
        multiplier = context.get_extra("multiplier")
        value = 2 * multiplier
        print("hello from databricks stdout")  # noqa: T201
        print("hello from databricks stderr", file=sys.stderr)  # noqa: T201
        context.log.info(f"{context.asset_key}: {2} * {multiplier} = {value}")
        context.report_asset_materialization(
            metadata={"value": value},
        )


CLUSTER_DEFAULTS = {
    "spark_version": "12.2.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 0,
}

TASK_KEY = "DAGSTER_PIPES_TASK"


# Create a new cluster on Databricks, yield the cluster_id, and then terminate the cluster
# on exit. This is useful for testing the PipesClient against an existing cluster.
@contextmanager
def temp_databricks_cluster(client: WorkspaceClient, forward_logs: bool) -> Iterator[str]:
    cluster_id = None
    try:
        # Need to make sure that nested dicts are wrapped in their SDK objects here (see
        # `use_inner_objects`). It's required by this API but apparently not by others. Hopefully
        # updating to a newer SDK will alleviate some of the annoyances around mixed acceptance of
        # objects from the SDK and their dict forms.
        cluster_spec = make_new_cluster_spec(forward_logs, use_inner_objects=True)
        cluster_details = client.clusters.create_and_wait(**cluster_spec)
        cluster_id = check.not_none(cluster_details.cluster_id)
        yield cluster_id
    finally:
        if cluster_id:
            client.clusters.delete(cluster_id)


def make_submit_task_dict(
    script_path: str,
    dagster_pipes_whl_path: str,
    forward_logs: bool,
    cluster_id: Optional[str] = None,
) -> Dict[str, Any]:
    submit_spec = {
        "libraries": [
            {"whl": dagster_pipes_whl_path},
        ],
        "task_key": TASK_KEY,
        "spark_python_task": {
            "python_file": f"dbfs:{script_path}",
            "source": jobs.Source.WORKSPACE,
        },
    }
    if cluster_id:
        submit_spec["existing_cluster_id"] = cluster_id
    else:
        submit_spec["new_cluster"] = make_new_cluster_spec(forward_logs)
    return submit_spec


def make_new_cluster_spec(forward_logs: bool, use_inner_objects: bool = False) -> Any:
    cluster_spec = CLUSTER_DEFAULTS.copy()
    if forward_logs:
        log_conf = {"dbfs": {"destination": "dbfs:/cluster-logs"}}
        cluster_spec["cluster_log_conf"] = (
            compute.ClusterLogConf.from_dict(log_conf) if use_inner_objects else log_conf
        )
    return cluster_spec


def make_submit_task(
    script_path: str,
    dagster_pipes_whl_path: str,
    forward_logs: bool,
    cluster_id: Optional[str] = None,
) -> jobs.SubmitTask:
    return jobs.SubmitTask.from_dict(
        make_submit_task_dict(
            script_path=script_path,
            dagster_pipes_whl_path=dagster_pipes_whl_path,
            forward_logs=forward_logs,
            cluster_id=cluster_id,
        )
    )


# Test both with and without log forwarding. This is important because the PipesClient spins up log
# readers before it knows the task specification
@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
@pytest.mark.parametrize("forward_logs", [True, False])
@pytest.mark.parametrize("use_existing_cluster", [True, False])
def test_pipes_client(
    capsys,
    databricks_client: WorkspaceClient,  # noqa: F811
    forward_logs: bool,
    use_existing_cluster: bool,
):
    if use_existing_cluster and forward_logs:
        # Two reasons for this: (a) logs are flushed every 5 minutes or on cluster termination.
        # If cluster termination is not tied to the end of the launched job, there is no mechanism
        # to wait for logs to be flushed. (b) The logs reader functions by forwarding stdout/stderr,
        # which is shared across all jobs on the cluster-- so there is no way to scope the
        # forwarding to just the target job.
        pytest.skip("Testing existing cluster with log forwarding currently does not work.")

    @asset
    def number_x(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):
        with ExitStack() as stack:
            dagster_pipes_whl_path = stack.enter_context(
                upload_dagster_pipes_whl(databricks_client)
            )
            script_path = stack.enter_context(
                temp_dbfs_script(databricks_client, script_fn=script_fn)
            )
            if use_existing_cluster:
                cluster_id = stack.enter_context(
                    temp_databricks_cluster(databricks_client, forward_logs)
                )
                task = make_submit_task(
                    script_path, dagster_pipes_whl_path, forward_logs, cluster_id
                )
            else:
                task = make_submit_task(script_path, dagster_pipes_whl_path, forward_logs)
            return pipes_client.run(
                task=task,
                context=context,
                extras={"multiplier": 2, "storage_root": "fake"},
            ).get_results()

    result = materialize(
        [number_x],
        resources={
            "pipes_client": PipesDatabricksClient(
                databricks_client,
            )
        },
        raise_on_error=False,
    )
    assert result.success
    mats = result.asset_materializations_for_node(number_x.op.name)
    assert mats[0].metadata["value"].value == 4
    if forward_logs:
        captured = capsys.readouterr()
        assert re.search(r"hello from databricks stdout\n", captured.out, re.MULTILINE)
        assert re.search(r"hello from databricks stderr\n", captured.err, re.MULTILINE)


@pytest.mark.skipif(IS_BUILDKITE, reason="Not configured to run on BK yet.")
def test_nonexistent_entry_point(databricks_client: WorkspaceClient):  # noqa: F811
    @asset
    def fake(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):
        task = make_submit_task("/fake/fake", "/fake/fake", forward_logs=False)
        return pipes_client.run(task=task, context=context).get_results()

    with pytest.raises(DagsterPipesExecutionError, match=r"Cannot read the python file"):
        materialize(
            [fake],
            resources={"pipes_client": PipesDatabricksClient(databricks_client)},
        )
