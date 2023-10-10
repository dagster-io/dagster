import json
import time
from contextlib import contextmanager
from typing import Any, Dict, Mapping, Optional

import dagster._check as check
import yaml
from dagster import ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials
from pydantic import Field

from .configs import define_dataproc_create_cluster_config
from .types import DataprocError

TWENTY_MINUTES = 20 * 60
DEFAULT_ITER_TIME_SEC = 5


class DataprocClient:
    """Builds a client to the dataproc API."""

    def __init__(self, config):
        # Use Application Default Credentials to check the
        # GOOGLE_APPLICATION_CREDENTIALS environment variable
        # for the location of the service account key file.
        credentials = GoogleCredentials.get_application_default()

        # See https://github.com/googleapis/google-api-python-client/issues/299 for the
        # cache_discovery=False configuration below
        self.dataproc = build("dataproc", "v1", credentials=credentials, cache_discovery=False)

        self.config = config

        (self.project_id, self.region, self.cluster_name, self.cluster_config) = (
            self.config.get(k) for k in ("projectId", "region", "clusterName", "cluster_config")
        )

    @property
    def dataproc_clusters(self):
        return (
            # Google APIs dynamically genned, so pylint pukes
            self.dataproc.projects()
            .regions()
            .clusters()
        )

    @property
    def dataproc_jobs(self):
        return (
            # Google APIs dynamically genned, so pylint pukes
            self.dataproc.projects()
            .regions()
            .jobs()
        )

    def create_cluster(self):
        (
            self.dataproc_clusters.create(
                projectId=self.project_id,
                region=self.region,
                body={
                    "projectId": self.project_id,
                    "clusterName": self.cluster_name,
                    "config": self.cluster_config,
                },
            ).execute()
        )

        def iter_fn():
            # TODO: Add logging
            # See: https://bit.ly/2UW5JaN
            cluster = self.get_cluster()
            return cluster["status"]["state"] in {"RUNNING", "UPDATING"}

        done = DataprocClient._iter_and_sleep_until_ready(iter_fn)
        if not done:
            cluster = self.get_cluster()
            raise DataprocError(
                "Could not provision cluster -- status: %s" % str(cluster["status"])
            )

    def get_cluster(self):
        return self.dataproc_clusters.get(
            projectId=self.project_id, region=self.region, clusterName=self.cluster_name
        ).execute()

    def delete_cluster(self):
        return self.dataproc_clusters.delete(
            projectId=self.project_id, region=self.region, clusterName=self.cluster_name
        ).execute()

    def submit_job(self, job_details):
        return self.dataproc_jobs.submit(
            projectId=self.project_id, region=self.region, body=job_details
        ).execute()

    def get_job(self, job_id):
        return self.dataproc_jobs.get(
            projectId=self.project_id, region=self.region, jobId=job_id
        ).execute()

    def wait_for_job(self, job_id, wait_timeout=TWENTY_MINUTES):
        """This method polls job status every 5 seconds."""

        # TODO: Add logging here print('Waiting for job ID {} to finish...'.format(job_id))
        def iter_fn():
            # See: https://bit.ly/2Lg2tHr
            result = self.get_job(job_id)

            # Handle exceptions
            if result["status"]["state"] in {"CANCELLED", "ERROR"}:
                raise DataprocError("Job error: %s" % str(result["status"]))

            if result["status"]["state"] == "DONE":
                return True

            return False

        done = DataprocClient._iter_and_sleep_until_ready(iter_fn, max_wait_time_sec=wait_timeout)
        if not done:
            job = self.get_job(job_id)
            raise DataprocError("Job run timed out: %s" % str(job["status"]))

    @staticmethod
    def _iter_and_sleep_until_ready(
        callable_fn, max_wait_time_sec=TWENTY_MINUTES, iter_time=DEFAULT_ITER_TIME_SEC
    ):
        """Iterates and sleeps until callable_fn returns true."""
        # Wait for cluster ready state
        ready, curr_iter = False, 0
        max_iter = max_wait_time_sec / iter_time
        while not ready and curr_iter < max_iter:
            ready = callable_fn()
            time.sleep(iter_time)
            curr_iter += 1

        # Will return false if ran up to max_iter without success
        return ready

    @contextmanager
    def cluster_context_manager(self):
        """Context manager allowing execution with a dataproc cluster.

        Example:
        .. code-block::
            with context.resources.dataproc.cluster as cluster:
                # do stuff...
        """
        self.create_cluster()
        try:
            yield self
        finally:
            self.delete_cluster()


class DataprocResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """Resource for connecting to a Dataproc cluster.

    Example:
        .. code-block::

            @asset
            def my_asset(dataproc: DataprocResource):
                with dataproc.get_client() as client:
                    # client is a dagster_gcp.DataprocClient
                    ...
    """

    project_id: str = Field(
        description=(
            "Required. Project ID for the project which the client acts on behalf of. Will be"
            " passed when creating a dataset/job."
        )
    )
    region: str = Field(description="The GCP region.")
    cluster_name: str = Field(
        description=(
            "Required. The cluster name. Cluster names within a project must be unique. Names of"
            " deleted clusters can be reused."
        )
    )
    cluster_config_yaml_path: Optional[str] = Field(
        default=None,
        description=(
            "Full path to a YAML file containing cluster configuration. See"
            " https://cloud.google.com/dataproc/docs/reference/rest/v1/ClusterConfig for"
            " configuration options. Only one of cluster_config_yaml_path,"
            " cluster_config_json_path, or cluster_config_dict may be provided."
        ),
    )
    cluster_config_json_path: Optional[str] = Field(
        default=None,
        description=(
            "Full path to a JSON file containing cluster configuration. See"
            " https://cloud.google.com/dataproc/docs/reference/rest/v1/ClusterConfig for"
            " configuration options. Only one of cluster_config_yaml_path,"
            " cluster_config_json_path, or cluster_config_dict may be provided."
        ),
    )
    cluster_config_dict: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Python dictionary containing cluster configuration. See"
            " https://cloud.google.com/dataproc/docs/reference/rest/v1/ClusterConfig for"
            " configuration options. Only one of cluster_config_yaml_path,"
            " cluster_config_json_path, or cluster_config_dict may be provided."
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _read_yaml_config(self, path: str) -> Mapping[str, Any]:
        with open(path, "r", encoding="utf8") as f:
            return yaml.safe_load(f)

    def _read_json_config(self, path: str) -> Mapping[str, Any]:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)

    def _get_cluster_config(self) -> Optional[Mapping[str, Any]]:
        methods = 0
        methods += 1 if self.cluster_config_dict is not None else 0
        methods += 1 if self.cluster_config_json_path is not None else 0
        methods += 1 if self.cluster_config_yaml_path is not None else 0

        # ensure that at most 1 method is provided
        check.invariant(
            methods <= 1,
            "Dataproc Resource: Incorrect config: Cannot provide cluster config multiple ways."
            " Choose one of cluster_config_dict, cluster_config_json_path, or"
            " cluster_config_yaml_path",
        )

        cluster_config = None
        if self.cluster_config_json_path:
            cluster_config = self._read_json_config(self.cluster_config_json_path)
        elif self.cluster_config_yaml_path:
            cluster_config = self._read_yaml_config(self.cluster_config_yaml_path)
        elif self.cluster_config_dict:
            cluster_config = self.cluster_config_dict

        return cluster_config

    def get_client(self) -> DataprocClient:
        cluster_config = self._get_cluster_config()

        client_config_dict = {
            "projectId": self.project_id,
            "region": self.region,
            "clusterName": self.cluster_name,
            "cluster_config": cluster_config,
        }

        return DataprocClient(config=client_config_dict)

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(
    config_schema=define_dataproc_create_cluster_config(),
    description="Manage a Dataproc cluster resource",
)
def dataproc_resource(context):
    return DataprocClient(context.resource_config)
