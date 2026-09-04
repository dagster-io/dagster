from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from typing import Any

from dagster._annotations import preview
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import PipesContextInjector, PipesMessageReader
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import PipesEnvContextInjector, PipesTempFileMessageReader
from prefect import Task
from prefect.settings import PREFECT_API_KEY, PREFECT_API_URL, temporary_settings

from dagster_prefect.pipes import BasePipesPrefectClient, PrefectRun

# The task argument carrying the Pipes bootstrap payload. A task worker's environment is
# fixed when the worker starts, so an argument is the only channel into a background task.
PIPES_PARAMS_TASK_ARGUMENT = "dagster_pipes_params"


@preview
class PipesPrefectTaskClient(BasePipesPrefectClient):
    """Launches a Prefect background task and materializes when its task run finishes.

    The task must accept a ``dagster_pipes_params`` argument and open a Pipes session with it:

    .. code-block:: python

        from dagster_pipes import PipesMappingParamsLoader, open_dagster_pipes

        @task
        def summarize(as_of: str, dagster_pipes_params: dict[str, str] | None = None) -> None:
            with open_dagster_pipes(
                params_loader=PipesMappingParamsLoader(dagster_pipes_params or {})
            ) as pipes:
                pipes.report_asset_materialization(metadata={"rows": 100})

    Then launch it from an asset:

    .. code-block:: python

        @dg.asset
        def orders_summary(context: dg.AssetExecutionContext, prefect_tasks: PipesPrefectTaskClient):
            return prefect_tasks.run(
                context=context, task=summarize, parameters={"as_of": "latest"}
            ).get_materialize_result()

    A task worker must be serving the task (``prefect task serve``), otherwise the task run
    is created and never picked up, and this blocks until the Dagster run is terminated.
    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _launch(  # ty: ignore[invalid-method-override]
        self,
        *,
        context: OpExecutionContext | AssetExecutionContext,
        session: PipesSession,
        task: Task,
        parameters: Mapping[str, Any] | None = None,
        args: Sequence[Any] | None = None,
        partition_parameter: str | None = None,
        partition_window_parameters: tuple[str, str] | None = None,
    ) -> PrefectRun:
        """Submit the task with `.delay()`, which returns as soon as the run is created."""
        task_parameters = {
            **(parameters or {}),
            **self._partition_parameters(context, partition_parameter, partition_window_parameters),
            # Encoded rather than raw so it survives Prefect's parameter serialization, and
            # so `PipesMappingParamsLoader` on the task side can read it as-is.
            PIPES_PARAMS_TASK_ARGUMENT: dict(session.get_bootstrap_env_vars()),
        }

        with self._prefect_settings():
            future = task.delay(*(args or ()), **task_parameters)

        return PrefectRun(kind="task-run", id=future.task_run_id)

    def _default_context_injector(self) -> PipesContextInjector:
        # Inlines the context into the payload, so nothing external has to store it.
        return PipesEnvContextInjector()

    def _default_message_reader(self) -> PipesMessageReader:
        # Only correct when the task worker shares a filesystem with the Dagster step, which
        # is the case for a worker on the same host. Pass a blob-store reader otherwise.
        return PipesTempFileMessageReader()

    @contextmanager
    def _prefect_settings(self):
        """Point `.delay()` at the resource's Prefect server.

        `Task.delay` talks to whatever server the ambient Prefect settings name, so without
        this the task would be submitted somewhere other than where the client polls.
        """
        updates: dict[Any, Any] = {PREFECT_API_URL: self.prefect.api_url}
        if self.prefect.api_key:
            updates[PREFECT_API_KEY] = self.prefect.api_key
        with temporary_settings(updates):
            yield
