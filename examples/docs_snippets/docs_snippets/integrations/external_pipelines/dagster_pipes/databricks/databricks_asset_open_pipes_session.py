import os
import sys

from dagster_databricks import PipesDbfsContextInjector, PipesDbfsMessageReader
from dagster_databricks.pipes import PipesDbfsLogReader

from dagster import AssetExecutionContext, asset, open_pipes_session
from databricks.sdk import WorkspaceClient


@asset
def databricks_asset(context: AssetExecutionContext):
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )

    # Arbitrary json-serializable data you want access to from the `PipesContext`
    # in the Databricks runtime. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    # Sets up Pipes communications channels
    with open_pipes_session(
        context=context,
        extras=extras,
        context_injector=PipesDbfsContextInjector(client=client),
        message_reader=PipesDbfsMessageReader(
            client=client,
            # These log readers are optional. If you provide them, then you must set the
            # `new_cluster.cluster_log_conf.dbfs.destination` field in the job you submit to a valid
            # DBFS path. This will configure Databricks to write stdout/stderr to the specified
            # location every 5 minutes. Dagster will poll this location and forward the
            # stdout/stderr logs every time they are updated to the orchestration process
            # stdout/stderr.
            log_readers=[
                PipesDbfsLogReader(
                    client=client, remote_log_name="stdout", target_stream=sys.stdout
                ),
                PipesDbfsLogReader(
                    client=client, remote_log_name="stderr", target_stream=sys.stderr
                ),
            ],
        ),
    ) as pipes_session:
        ##### Option (1)
        # NON-STREAMING. Just pass the necessary environment variables down.
        # During execution, all reported materializations are buffered on the
        # `pipes_session`. Yield them all after Databricks execution is finished.

        # Dict[str, str] with environment variables containing Pipes comms info.
        env_vars = pipes_session.get_bootstrap_env_vars()

        # Some function that handles launching/monitoring of the Databricks job.
        # It must ensure that the `env_vars` are set on the executing cluster.
        custom_databricks_launch_code(env_vars)  # type: ignore  # noqa: F821

        ##### Option (2)
        # STREAMING. Pass `pipes_session` down. During execution, you can yield any
        # asset materializations that have been reported by calling `
        # pipes_session.get_results()` as often as you like. `get_results` returns
        # an iterator that your custom code can `yield from` to forward the
        # results back to the materialize function. Note you will need to extract
        # the env vars by calling `pipes_session.get_pipes_bootstrap_env_vars()`,
        # and launch the Databricks job in the same way as with (1).

        # The function should return an `Iterator[MaterializeResult]`.
        yield from custom_databricks_launch_code(pipes_session)  # type: ignore  # noqa: F821

    # With either option (1) or (2), this is required to yield any remaining
    # buffered results.
    yield from pipes_session.get_results()
