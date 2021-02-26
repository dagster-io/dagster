import time
from contextlib import contextmanager

from dagster import resource
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

from .configs import define_dataproc_create_cluster_config
from .types import DataprocError

TWENTY_MINUTES = 20 * 60
DEFAULT_ITER_TIME_SEC = 5


class DataprocResource:
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
            # pylint: disable=no-member
            self.dataproc.projects()
            .regions()
            .clusters()
        )

    @property
    def dataproc_jobs(self):
        return (
            # Google APIs dynamically genned, so pylint pukes
            # pylint: disable=no-member
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

        done = DataprocResource._iter_and_sleep_until_ready(iter_fn)
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

    def wait_for_job(self, job_id):
        """This method polls job status every 5 seconds"""
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

        done = DataprocResource._iter_and_sleep_until_ready(iter_fn)
        if not done:
            job = self.get_job(job_id)
            raise DataprocError("Job run timed out: %s" % str(job["status"]))

    @staticmethod
    def _iter_and_sleep_until_ready(
        callable_fn, max_wait_time_sec=TWENTY_MINUTES, iter_time=DEFAULT_ITER_TIME_SEC
    ):
        """Iterates and sleeps until callable_fn returns true"""
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
        """This context manager gives syntactic sugar so you can run:

        with context.resources.dataproc.cluster as cluster:
            # do stuff...
        """
        self.create_cluster()
        try:
            yield self
        finally:
            self.delete_cluster()


@resource(
    config_schema=define_dataproc_create_cluster_config(),
    description="Manage a Dataproc cluster resource",
)
def dataproc_resource(context):
    return DataprocResource(context.resource_config)
