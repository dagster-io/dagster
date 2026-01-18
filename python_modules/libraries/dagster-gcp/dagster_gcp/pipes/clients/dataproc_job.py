import re
import time
from collections.abc import Mapping, Sequence
from typing import Any, Optional, TypedDict, Union

import dagster._check as check
from dagster import PipesClient
from dagster._annotations import preview, public
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session
from google.api_core.retry import Retry
from google.cloud.dataproc_v1 import JobControllerClient
from google.cloud.dataproc_v1.types.jobs import Job, JobStatus, SubmitJobRequest
from typing_extensions import NotRequired

SERVICE_NAME = "Dataproc"


class SubmitJobParams(TypedDict):
    request: NotRequired[SubmitJobRequest]
    project_id: NotRequired[str]
    region: NotRequired[str]
    job: NotRequired[Job]
    retry: NotRequired[Retry]
    timeout: NotRequired[float]
    metadata: NotRequired[Sequence[tuple[str, Union[str, bytes]]]]


def _inject_pipes_args_into_list(args: Sequence[str], session: PipesSession) -> list[str]:
    args_list = list(args)
    for key, value in session.get_bootstrap_cli_arguments().items():
        args_list.extend([key, value])
    return args_list


# Only lowercase letters, numbers, and dashes are allowed. The value must start with lowercase letter or number and end with a lowercase letter or number.
DATAPROC_LABELS_PATTERN = r"[^a-z0-9-]|^[^a-z0-9]|[^a-z0-9]$"


def _sanitize_labels(labels: Mapping[str, Any]) -> dict[str, str]:
    # only alphanumeric characters, hyphens, and underscores are allowed in labels
    return {
        re.sub(DATAPROC_LABELS_PATTERN, "-", k.lower()): re.sub(
            DATAPROC_LABELS_PATTERN, "-", v.lower()
        )
        for k, v in labels.items()
    }


JOB_TYPES_WITH_ARGS = [
    "hadoop_job",
    "spark_job",
    "pyspark_job",
    "spark_r_job",
    "flink_job",
]


@public
@preview
class PipesDataprocJobClient(PipesClient, TreatAsResourceParam):
    """A pipes client for running workloads on GCP Dataproc in Job mode.

    Args:
        client (Optional[google.cloud.dataproc_v1.JobControllerClient]): The GCP Dataproc client to use.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the GCP Dataproc job. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (PipesMessageReader): A message reader to use to read messages
            from the GCP Dataproc job. For example, :py:class:`PipesGCSMessageReader`.
        forward_termination (bool): Whether to cancel the GCP Dataproc job if the Dagster process receives a termination signal.
        poll_interval (float): The interval in seconds to poll the GCP Dataproc job for status updates. Defaults to 5 seconds.
    """

    SERVICE_NAME = SERVICE_NAME

    def __init__(
        self,
        message_reader: PipesMessageReader,
        client: Optional[JobControllerClient] = None,
        context_injector: Optional[PipesContextInjector] = None,
        forward_termination: bool = True,
        poll_interval: float = 5.0,
    ):
        self._client: JobControllerClient = client or JobControllerClient()
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")
        self.poll_interval = poll_interval

    @property
    def client(self) -> JobControllerClient:
        return self._client

    @property
    def context_injector(self) -> PipesContextInjector:
        return self._context_injector

    @property
    def message_reader(self) -> PipesMessageReader:
        return self._message_reader

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        submit_job_params: SubmitJobParams,
        extras: Optional[dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Run a job on GCP Dataproc, enriched with the pipes protocol.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            submit_job_params (SubmitJobParams): Parameters for the ``JobControllerClient.submit_job`` call.
                See `Google Cloud SDK Documentation <https://cloud.google.com/python/docs/reference/dataproc/latest/google.cloud.dataproc_v1.services.job_controller.JobControllerClient#google_cloud_dataproc_v1_services_job_controller_JobControllerClient_submit_job>`_
            extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self.message_reader,
            context_injector=self.context_injector,
            extras=extras,
        ) as session:
            submit_job_params = self._enrich_submit_job_params(
                context, session=session, params=submit_job_params
            )
            job = self._start(context, params=submit_job_params)
            try:
                job = self._wait_for_completion(context, job=job, params=submit_job_params)
                context.log.info(f"[pipes] {self.SERVICE_NAME} job is complete!")
                return PipesClientCompletedInvocation(
                    session, metadata=self._extract_dagster_metadata(job)
                )

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        f"[pipes] Dagster process interrupted! Will terminate external {self.SERVICE_NAME} job."
                    )
                    self._terminate(context, params=submit_job_params, job=job)
                raise

    def _request_parameter_is_used(self, params: SubmitJobParams) -> bool:
        """Google Cloud SDK has a weird API where some parameters can either be passed directly
        or as part of a request object. This method checks if the request object is used in the user-provided parameters.
        """
        if params.get("request"):
            return True
        else:
            return False

    def _enrich_submit_job_params(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        params: SubmitJobParams,
    ) -> SubmitJobParams:
        request_is_used = self._request_parameter_is_used(params)

        # inject Dagster labels
        if not request_is_used:
            job = params["job"]  # type: ignore
        else:
            job: Job = params["request"].job  # type: ignore

        job.labels = {
            **(job.labels or {}),
            **_sanitize_labels(session.default_remote_invocation_info),
        }

        # inject arguments for job types which have them

        for job_type in JOB_TYPES_WITH_ARGS:
            if hasattr(job, job_type) and getattr(job, job_type):
                job_params = getattr(job, job_type)
                job_params.args = _inject_pipes_args_into_list(job_params.args or [], session)

        # TODO: potentially support other job types like "pig_job", "hive_job", "spark_sql_job"
        # via parameters like "properties"

        return params

    def _start(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        params: SubmitJobParams,
    ) -> Job:
        job = self.client.submit_job(**params)

        context.log.info(f"[pipes] {self.SERVICE_NAME} job started with ID {job.job_uuid}")

        return job

    def _wait_for_completion(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        params: SubmitJobParams,
        job: Job,
    ) -> Job:
        project_id, region = self._get_project_id_and_region(params)

        while not job.done:
            time.sleep(self.poll_interval)
            job = self.client.get_job(job_id=job.job_uuid, project_id=project_id, region=region)

        # possible states: https://cloud.google.com/dataproc/docs/concepts/jobs/life-of-a-job
        if job.status.state != JobStatus.State.DONE:
            raise RuntimeError(f"{self.SERVICE_NAME} job failed with error: {job.status.details}")
        else:
            return job

    def _get_project_id_and_region(
        self, params: SubmitJobParams
    ) -> tuple[Optional[str], Optional[str]]:
        request_is_used = self._request_parameter_is_used(params)

        if request_is_used:
            return params["request"].project_id, params["request"].region  # type: ignore
        else:
            return params.get("project_id"), params.get("region")

    def _extract_dagster_metadata(self, job: Job) -> RawMetadataMapping:
        metadata: RawMetadataMapping = {}

        metadata["GCP Dataproc Job ID"] = job.job_uuid

        return metadata

    def _terminate(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        params: SubmitJobParams,
        job: Job,
    ):
        project_id, region = self._get_project_id_and_region(params)

        context.log.info(f"[pipes] Terminating {self.SERVICE_NAME} job {job.job_uuid}")

        self.client.cancel_job(job_id=job.job_uuid, project_id=project_id, region=region)
