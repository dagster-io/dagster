import base64
import logging
import time
from typing import Any, Mapping, Optional

import dagster
import dagster._check as check
import dagster_pyspark
import requests.exceptions
from dagster._annotations import public
from databricks_api import DatabricksAPI
from databricks_cli.sdk import ApiClient, ClusterService, DbfsService, JobsService

import dagster_databricks

from .types import (
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
    DatabricksRunState,
)
from .version import __version__

# wait at most 24 hours by default for run execution
DEFAULT_RUN_MAX_WAIT_TIME_SEC = 24 * 60 * 60


class DatabricksError(Exception):
    pass


class DatabricksClient:
    """A thin wrapper over the Databricks REST API."""

    def __init__(self, host: str, token: str, workspace_id: Optional[str] = None):
        self.host = host
        self.workspace_id = workspace_id

        # TODO: This is the old shim client that we were previously using. Arguably this is
        # confusing for users to use since this is an unofficial wrapper around the documented
        # Databricks REST API. We should consider removing this in the future.
        self.client = DatabricksAPI(host=host, token=token)
        self.__setup_user_agent(self.client.client)

        # Expose an interface directly to the official Databricks API client.
        self._api_client = ApiClient(host=host, token=token)
        self.__setup_user_agent(self._api_client)

    def __setup_user_agent(self, client: ApiClient) -> None:
        """Overrides the user agent for the Databricks API client."""
        client.default_headers["user-agent"] = f"dagster-databricks/{__version__}"

    @public
    @property
    def api_client(self) -> ApiClient:
        """Retrieve a reference to the underlying Databricks API client. For more information,
        see the `Databricks Python API <https://docs.databricks.com/dev-tools/python-api.html>`_.

        **Examples:**

        .. code-block:: python

            from dagster import op
            from databricks_cli.jobs.api import JobsApi
            from databricks_cli.runs.api import RunsApi

            @op(required_resource_keys={"databricks_client"})
            def op1(context):
                # Initialize the Databricks Jobs API
                jobs_client = JobsApi(context.resources.databricks_client.api_client)
                runs_client = RunsApi(context.resources.databricks_client.api_client)

                # Example 1: Run a Databricks job with some parameters.
                jobs_client.run_now(...)

                # Example 2: Trigger a one-time run of a Databricks workload.
                runs_client.submit_run(...)

                # Example 3: Get an existing run.
                runs_client.get_run(...)

                # Example 4: Cancel a run.
                runs_client.cancel_run(...)

        Returns:
            ApiClient: The authenticated Databricks API client.
        """
        return self._api_client

    def read_file(self, dbfs_path: str, block_size: int = 1024**2) -> bytes:
        """Read a file from DBFS to a **byte string**."""
        if dbfs_path.startswith("dbfs://"):
            dbfs_path = dbfs_path[7:]

        data = b""
        bytes_read = 0
        dbfs_service = DbfsService(self.api_client)

        jdoc = dbfs_service.read(path=dbfs_path, length=block_size)
        data += base64.b64decode(jdoc["data"])
        while jdoc["bytes_read"] == block_size:
            bytes_read += jdoc["bytes_read"]
            jdoc = dbfs_service.read(path=dbfs_path, offset=bytes_read, length=block_size)
            data += base64.b64decode(jdoc["data"])

        return data

    def put_file(
        self, file_obj, dbfs_path: str, overwrite: bool = False, block_size: int = 1024**2
    ) -> None:
        """Upload an arbitrary large file to DBFS.

        This doesn't use the DBFS `Put` API because that endpoint is limited to 1MB.
        """
        if dbfs_path.startswith("dbfs://"):
            dbfs_path = dbfs_path[7:]

        dbfs_service = DbfsService(self.api_client)

        create_response = dbfs_service.create(path=dbfs_path, overwrite=overwrite)
        handle = create_response["handle"]

        block = file_obj.read(block_size)
        while block:
            data = base64.b64encode(block).decode("utf-8")
            dbfs_service.add_block(data=data, handle=handle)
            block = file_obj.read(block_size)

        dbfs_service.close(handle=handle)

    def get_run_state(self, databricks_run_id: int) -> "DatabricksRunState":
        """Get the state of a run by Databricks run ID.

        Return a `DatabricksRunState` object. Note that the `result_state`
        attribute may be `None` if the run hasn't yet terminated.
        """
        run = JobsService(self.api_client).get_run(databricks_run_id)
        state = run["state"]
        result_state = (
            DatabricksRunResultState(state.get("result_state"))
            if state.get("result_state")
            else None
        )

        return DatabricksRunState(
            life_cycle_state=DatabricksRunLifeCycleState(state["life_cycle_state"]),
            result_state=result_state,
            state_message=state["state_message"],
        )

    def poll_run_state(
        self,
        logger: logging.Logger,
        start_poll_time: float,
        databricks_run_id: int,
        max_wait_time_sec: float,
        verbose_logs: bool = True,
    ) -> bool:
        run_state = self.get_run_state(databricks_run_id)

        if run_state.has_terminated():
            if run_state.is_successful():
                logger.info(f"Run `{databricks_run_id}` completed successfully.")
                return True
            else:
                error_message = (
                    f"Run `{databricks_run_id}` failed with result state:"
                    f" `{run_state.result_state}`. Message: {run_state.state_message}."
                )
                logger.error(error_message)
                raise DatabricksError(error_message)
        else:
            if verbose_logs:
                logger.debug(f"Run `{databricks_run_id}` in state {run_state}.")
        if time.time() - start_poll_time > max_wait_time_sec:
            raise DatabricksError(
                f"Run `{databricks_run_id}` took more than {max_wait_time_sec}s to complete."
                " Failing the run."
            )
        return False

    def wait_for_run_to_complete(
        self,
        logger: logging.Logger,
        databricks_run_id: int,
        poll_interval_sec: float,
        max_wait_time_sec: int,
        verbose_logs: bool = True,
    ) -> None:
        logger.info(f"Waiting for Databricks run `{databricks_run_id}` to complete...")

        start_poll_time = time.time()
        while True:
            if self.poll_run_state(
                logger=logger,
                start_poll_time=start_poll_time,
                databricks_run_id=databricks_run_id,
                max_wait_time_sec=max_wait_time_sec,
                verbose_logs=verbose_logs,
            ):
                return

            time.sleep(poll_interval_sec)


class DatabricksJobRunner:
    """Submits jobs created using Dagster config to Databricks, and monitors their progress."""

    def __init__(
        self,
        host: str,
        token: str,
        poll_interval_sec: float = 5,
        max_wait_time_sec: int = DEFAULT_RUN_MAX_WAIT_TIME_SEC,
    ):
        """Args:

        host (str): Databricks host, e.g. https://uksouth.azuredatabricks.net
        token (str): Databricks token
        """
        self.host = check.str_param(host, "host")
        self.token = check.str_param(token, "token")
        self.poll_interval_sec = check.numeric_param(poll_interval_sec, "poll_interval_sec")
        self.max_wait_time_sec = check.int_param(max_wait_time_sec, "max_wait_time_sec")

        self._client: DatabricksClient = DatabricksClient(host=self.host, token=self.token)

    @property
    def client(self) -> DatabricksClient:
        """Return the underlying `DatabricksClient` object."""
        return self._client

    def submit_run(self, run_config: Mapping[str, Any], task: Mapping[str, Any]) -> int:
        """Submit a new run using the 'Runs submit' API."""
        existing_cluster_id = run_config["cluster"].get("existing")

        new_cluster = run_config["cluster"].get("new")

        # The Databricks API needs different keys to be present in API calls depending
        # on new/existing cluster, so we need to process the new_cluster
        # config first.
        if new_cluster:
            new_cluster = new_cluster.copy()

            nodes = new_cluster.pop("nodes")
            if "instance_pool_id" in nodes:
                new_cluster["instance_pool_id"] = nodes["instance_pool_id"]
            else:
                node_types = nodes["node_types"]
                new_cluster["node_type_id"] = node_types["node_type_id"]
                if "driver_node_type_id" in node_types:
                    new_cluster["driver_node_type_id"] = node_types["driver_node_type_id"]

            cluster_size = new_cluster.pop("size")
            if "num_workers" in cluster_size:
                new_cluster["num_workers"] = cluster_size["num_workers"]
            else:
                new_cluster["autoscale"] = cluster_size["autoscale"]

            tags = new_cluster.get("custom_tags", [])
            tags.append({"key": "__dagster_version", "value": dagster.__version__})
            new_cluster["custom_tags"] = tags

        check.invariant(
            existing_cluster_id is not None or new_cluster is not None,
            "Invalid value for run_config.cluster",
        )

        # We'll always need some libraries, namely dagster/dagster_databricks/dagster_pyspark,
        # since they're imported by our scripts.
        # Add them if they're not already added by users in config.
        libraries = list(run_config.get("libraries", []))
        install_default_libraries = run_config.get("install_default_libraries", True)
        if install_default_libraries:
            python_libraries = {
                x["pypi"]["package"].split("==")[0].replace("_", "-")
                for x in libraries
                if "pypi" in x
            }

            for library_name, library in [
                ("dagster", dagster),
                ("dagster-databricks", dagster_databricks),
                ("dagster-pyspark", dagster_pyspark),
            ]:
                if library_name not in python_libraries:
                    libraries.append(
                        {"pypi": {"package": "{}=={}".format(library_name, library.__version__)}}
                    )

        # Only one task should be able to be chosen really; make sure of that here.
        check.invariant(
            sum(
                task.get(key) is not None
                for key in [
                    "notebook_task",
                    "spark_python_task",
                    "spark_jar_task",
                    "spark_submit_task",
                ]
            )
            == 1,
            "Multiple tasks specified in Databricks run",
        )

        config = {
            "run_name": run_config.get("run_name"),
            "new_cluster": new_cluster,
            "existing_cluster_id": existing_cluster_id,
            "libraries": libraries,
            **task,
        }
        return JobsService(self.client.api_client).submit_run(**config)["run_id"]

    def retrieve_logs_for_run_id(self, log: logging.Logger, databricks_run_id: int):
        """Retrieve the stdout and stderr logs for a run."""
        api_client = self.client.api_client

        run = JobsService(api_client).get_run(databricks_run_id)
        cluster = ClusterService(api_client).get_cluster(run["cluster_instance"]["cluster_id"])
        log_config = cluster.get("cluster_log_conf")
        if log_config is None:
            log.warn(
                "Logs not configured for cluster {cluster} used for run {run}".format(
                    cluster=cluster["cluster_id"], run=databricks_run_id
                )
            )
            return None
        if "s3" in log_config:
            logs_prefix = log_config["s3"]["destination"]
            log.warn("Retrieving S3 logs not yet implemented")
            return None
        elif "dbfs" in log_config:
            logs_prefix = log_config["dbfs"]["destination"]
            stdout = self.wait_for_dbfs_logs(log, logs_prefix, cluster["cluster_id"], "stdout")
            stderr = self.wait_for_dbfs_logs(log, logs_prefix, cluster["cluster_id"], "stderr")
            return stdout, stderr

    def wait_for_dbfs_logs(
        self,
        log: logging.Logger,
        prefix,
        cluster_id,
        filename,
        waiter_delay: int = 10,
        waiter_max_attempts: int = 10,
    ) -> Optional[str]:
        """Attempt up to `waiter_max_attempts` attempts to get logs from DBFS."""
        path = "/".join([prefix, cluster_id, "driver", filename])
        log.info("Retrieving logs from {}".format(path))
        num_attempts = 0
        while num_attempts <= waiter_max_attempts:
            try:
                logs = self.client.read_file(path)
                return logs.decode("utf-8")
            except requests.exceptions.HTTPError:
                num_attempts += 1
                time.sleep(waiter_delay)
        log.warn("Could not retrieve cluster logs!")
