from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any
from uuid import UUID

from dagster import ConfigurableResource
from dagster._core.errors import DagsterInvariantViolationError
from prefect.client.orchestration import SyncPrefectClient
from prefect.client.schemas.objects import FlowRun, State, TaskRun
from prefect.exceptions import ObjectNotFound
from prefect.states import Cancelling
from pydantic import Field

# Prefect's UI is served from the API host without the `/api` suffix on an open-source
# server, but Prefect Cloud puts them on different hosts with different paths.
_API_URL_SUFFIX = "/api"


class PrefectResource(ConfigurableResource):
    """Client for the Prefect API.

    Wraps the calls the Prefect Pipes clients need: launching a deployment run, reading a
    run's state, canceling a flow run, and building links back into the Prefect UI.

    Examples:
        .. code-block:: python

            from dagster_prefect import PrefectResource

            resource = PrefectResource(
                api_url="http://127.0.0.1:4200/api",
                ui_url="http://127.0.0.1:4200",
            )
    """

    api_url: str = Field(
        description="URL of the Prefect API.",
        examples=[
            "http://127.0.0.1:4200/api",
            "https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>",
        ],
    )
    api_key: str | None = Field(
        default=None,
        description="API key used to authenticate with Prefect Cloud.",
        examples=['"{{ env.PREFECT_API_KEY }}"'],
        repr=False,
    )
    ui_url: str | None = Field(
        default=None,
        description=(
            "Base URL of the Prefect UI, used to link Dagster runs to the Prefect run that "
            "backs them. Defaults to `api_url` without its trailing `/api`, which is correct "
            "for an open-source Prefect server. Prefect Cloud serves its UI from a different "
            "host, so set this explicitly there."
        ),
        examples=[
            "http://127.0.0.1:4200",
            "https://app.prefect.cloud/account/<account-id>/workspace/<workspace-id>",
        ],
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @contextmanager
    def get_client(self) -> Iterator[SyncPrefectClient]:
        """Open a Prefect client scoped to this resource's config."""
        with SyncPrefectClient(api=self.api_url, api_key=self.api_key) as client:
            yield client

    def launch_deployment_run(
        self,
        deployment_name: str,
        *,
        parameters: Mapping[str, Any] | None = None,
        job_variables: Mapping[str, Any] | None = None,
        tags: Sequence[str] | None = None,
    ) -> FlowRun:
        """Create a flow run for a deployment, identified as ``flow-name/deployment-name``.

        The run is created but not waited on — a worker on the deployment's work pool picks
        it up.
        """
        with self.get_client() as client:
            try:
                deployment = client.read_deployment_by_name(deployment_name)
            except ObjectNotFound as err:
                # Prefect raises this with an empty message, which leaves nothing to debug.
                raise DagsterInvariantViolationError(
                    f'No Prefect deployment named "{deployment_name}".'
                ) from err
            return client.create_flow_run_from_deployment(
                deployment.id,
                parameters=dict(parameters) if parameters else None,
                job_variables=dict(job_variables) if job_variables else None,
                tags=list(tags) if tags else None,
            )

    def get_flow_run(self, flow_run_id: UUID | str) -> FlowRun:
        with self.get_client() as client:
            return client.read_flow_run(_as_uuid(flow_run_id))

    def get_task_run(self, task_run_id: UUID | str) -> TaskRun:
        with self.get_client() as client:
            return client.read_task_run(_as_uuid(task_run_id))

    def cancel_flow_run(self, flow_run_id: UUID | str) -> None:
        """Ask Prefect to cancel a flow run.

        Prefect moves the run to ``CANCELLING`` and the worker running it is responsible for
        finishing the job, so this returning does not mean the run has stopped.
        """
        with self.get_client() as client:
            client.set_flow_run_state(_as_uuid(flow_run_id), Cancelling())

    def flow_run_url(self, flow_run_id: UUID | str) -> str:
        return self._run_url("flow-run", flow_run_id)

    def task_run_url(self, task_run_id: UUID | str) -> str:
        return self._run_url("task-run", task_run_id)

    def _run_url(self, kind: str, run_id: UUID | str) -> str:
        # Mirrors the paths Prefect's own `url_for` builds. We don't call it because its
        # `default_base_url` only applies when the ambient Prefect settings carry no UI URL,
        # so a `PREFECT_UI_URL` in the environment would quietly outrank this resource's
        # own config.
        base_url = self.ui_url or self.api_url.rstrip("/").removesuffix(_API_URL_SUFFIX)
        return f"{base_url.rstrip('/')}/runs/{kind}/{run_id}"


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(value)


def is_successful_state(state: State | None) -> bool:
    """Whether a Prefect state means the work finished and succeeded.

    Only ``COMPLETED`` counts. ``CRASHED`` and ``CANCELLED`` are final but unsuccessful, so
    they fail the Dagster step rather than materializing an asset that was never produced.
    """
    return state is not None and state.is_completed()


def is_final_state(state: State | None) -> bool:
    """Whether a Prefect state means the work is over, successfully or not."""
    return state is not None and state.is_final()
