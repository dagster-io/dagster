from collections.abc import Mapping, Sequence
from typing import Any

from dagster._annotations import preview
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import PipesContextInjector, PipesMessageReader
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import PipesEnvContextInjector, PipesTempFileMessageReader

from dagster_prefect.pipes import BasePipesPrefectClient, PrefectRun

# Work pool job variable carrying environment overrides for a flow run. Present in the
# default base job template of every work pool type Prefect ships.
ENV_JOB_VARIABLE = "env"


@preview
class PipesPrefectDeploymentClient(BasePipesPrefectClient):
    """Launches a Prefect deployment run and materializes when the flow run finishes.

    The Pipes bootstrap payload is injected as environment variables through the deployment
    run's job variables, so the flow's own signature is untouched. The only change to the
    flow is opening a Pipes session:

    .. code-block:: python

        from dagster_pipes import open_dagster_pipes

        @flow
        def refresh_orders(as_of: str = "latest") -> None:
            with open_dagster_pipes() as pipes:
                pipes.report_asset_materialization(metadata={"rows": 100})

    That line is safe outside Dagster too — run standalone, `open_dagster_pipes` warns and
    returns a no-op context, so existing Prefect runs keep working.

    .. code-block:: python

        @dg.asset
        def orders_summary(
            context: dg.AssetExecutionContext, prefect_deployments: PipesPrefectDeploymentClient
        ):
            return prefect_deployments.run(
                context=context,
                deployment="refresh-orders/demo",
                parameters={"as_of": "latest"},
            ).get_materialize_result()

    Something has to execute the flow run — a worker on the deployment's work pool, a push
    work pool, or a Prefect Managed work pool. Without one the run stays scheduled and this
    blocks until the Dagster run is terminated.
    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _launch(  # ty: ignore[invalid-method-override]
        self,
        *,
        context: OpExecutionContext | AssetExecutionContext,
        session: PipesSession,
        deployment: str,
        parameters: Mapping[str, Any] | None = None,
        job_variables: Mapping[str, Any] | None = None,
        tags: Sequence[str] | None = None,
        partition_parameter: str | None = None,
        partition_window_parameters: tuple[str, str] | None = None,
    ) -> PrefectRun:
        """Create a flow run for `flow-name/deployment-name` and return without waiting."""
        flow_run = self.prefect.launch_deployment_run(
            deployment,
            parameters={
                **(parameters or {}),
                **self._partition_parameters(
                    context, partition_parameter, partition_window_parameters
                ),
            },
            job_variables=self._job_variables_with_pipes_env(session, job_variables),
            tags=tags,
        )
        return PrefectRun(kind="flow-run", id=flow_run.id)

    def _default_context_injector(self) -> PipesContextInjector:
        # Inlines the context into the env vars, so nothing external has to store it and the
        # flow can use the default `PipesEnvVarParamsLoader`.
        return PipesEnvContextInjector()

    def _default_message_reader(self) -> PipesMessageReader:
        # Only correct when the worker executing the flow shares a filesystem with the
        # Dagster step. Pass a blob-store reader for a worker anywhere else.
        return PipesTempFileMessageReader()

    def _job_variables_with_pipes_env(
        self, session: PipesSession, job_variables: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        job_variables = dict(job_variables or {})
        # Pipes variables last: a caller must not be able to shadow them.
        env = {
            **job_variables.get(ENV_JOB_VARIABLE, {}),
            **session.get_bootstrap_env_vars(),
        }
        return {**job_variables, ENV_JOB_VARIABLE: env}
