import base64
import logging
import time
from typing import IO, Any, Mapping, Optional, Tuple, Union, cast

import dagster
import dagster._check as check
import dagster_pyspark
import databricks_api
import databricks_cli.sdk
import requests.exceptions
from dagster._annotations import deprecated, public
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import compute, jobs
from typing_extensions import Final

import dagster_databricks

from .types import (
    DatabricksRunState,
)
from .version import __version__

# wait at most 24 hours by default for run execution
DEFAULT_RUN_MAX_WAIT_TIME_SEC: Final = 24 * 60 * 60


class DatabricksError(Exception):
    pass


class DatabricksClient:
    """A thin wrapper over the Databricks REST API."""

    def __init__(
        self,
        host: str,
        token: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        self.host = host
        self.workspace_id = workspace_id

        self._workspace_client = WorkspaceClient(
            host=host,
            token=token,
            client_id=oauth_client_id,
            client_secret=oauth_client_secret,
            product="dagster-databricks",
            product_version=__version__,
        )

        # TODO: This is the old shim client that we were previously using. Arguably this is
        # confusing for users to use since this is an unofficial wrapper around the documented
        # Databricks REST API. We should consider removing this in the next minor release.
        if token:
            self._client = databricks_api.DatabricksAPI(host=host, token=token)
            self.__setup_user_agent(self._client.client)
            # TODO: This is the old `databricks_cli` client that was previously recommended by Databricks.
            # It is no longer supported and should be removed in favour of `databricks-sdk` in the next
            # minor release.
            self._api_client = databricks_cli.sdk.ApiClient(host=host, token=token)
            self.__setup_user_agent(self._api_client)
        else:
            self._client = None
            self._api_client = None

    def __setup_user_agent(
        self,
        client: Union[WorkspaceClient, databricks_api.DatabricksAPI, databricks_cli.sdk.ApiClient],
    ) -> None:
        """Overrides the user agent for the Databricks API client."""
        client.default_headers["user-agent"] = f"dagster-databricks/{__version__}"

    @deprecated(
        breaking_version="0.21.0", additional_warn_text="Use `workspace_client` property instead."
    )
    @public
    @property
    def client(self) -> databricks_api.DatabricksAPI:
        """Retrieve the legacy Databricks API client. Note: accessing this property will throw an exception if oauth
        credentials are used to initialize the DatabricksClient, because oauth credentials are not supported by the
        legacy Databricks API client.
        """
        if self._client is None:
            raise ValueError(
                "Legacy Databricks API client from `databricks-api` was not initialized because"
                " oauth credentials were used instead of an access token. This legacy Databricks"
                " API client is not supported when using oauth credentials. Use the"
                " `workspace_client` property instead."
            )
        return self._client

    @client.setter
    def client(self, value: Optional[databricks_api.DatabricksAPI]) -> None:
        self._client = value

    @deprecated(
        breaking_version="0.21.0", additional_warn_text="Use `workspace_client` property instead."
    )
    @public
    @property
    def api_client(self) -> databricks_cli.sdk.ApiClient:
        """Retrieve a reference to the underlying Databricks API client. For more information,
        see the `Databricks Python API <https://docs.databricks.com/dev-tools/python-api.html>`_.
        Noe: accessing this property will throw an exception if oauth credentials are used to initialize the
        DatabricksClient, because oauth credentials are not supported by the legacy Databricks API client.
        **Examples:**.

        .. code-block:: python

            from dagster import op
            from databricks_cli.jobs.api import JobsApi
            from databricks_cli.runs.api import RunsApi
            from databricks.sdk import WorkspaceClient

            @op(required_resource_keys={"databricks_client"})
            def op1(context):
                # Initialize the Databricks Jobs API
                jobs_client = JobsApi(context.resources.databricks_client.api_client)
                runs_client = RunsApi(context.resources.databricks_client.api_client)
                client = context.resources.databricks_client.api_client

                # Example 1: Run a Databricks job with some parameters.
                jobs_client.run_now(...)
                client.jobs.run_now(...)

                # Example 2: Trigger a one-time run of a Databricks workload.
                runs_client.submit_run(...)
                client.jobs.submit(...)

                # Example 3: Get an existing run.
                runs_client.get_run(...)
                client.jobs.get_run(...)

                # Example 4: Cancel a run.
                runs_client.cancel_run(...)
                client.jobs.cancel_run(...)

        Returns:
            ApiClient: The authenticated Databricks API client.
        """
        if self._api_client is None:
            raise ValueError(
                "Legacy Databricks API client from `databricks-cli` was not initialized because"
                " oauth credentials were used instead of an access token. This legacy Databricks"
                " API client is not supported when using oauth credentials. Use the"
                " `workspace_client` property instead."
            )
        return self._api_client

    @public
    @property
    def workspace_client(self) -> WorkspaceClient:
        """Retrieve a reference to the underlying Databricks Workspace client. For more information,
        see the `Databricks SDK for Python <https://docs.databricks.com/dev-tools/sdk-python.html>`_.

        **Examples:**

        .. code-block:: python

            from dagster import op
            from databricks.sdk import WorkspaceClient

            @op(required_resource_keys={"databricks_client"})
            def op1(context):
                # Initialize the Databricks Jobs API
                client = context.resources.databricks_client.api_client

                # Example 1: Run a Databricks job with some parameters.
                client.jobs.run_now(...)

                # Example 2: Trigger a one-time run of a Databricks workload.
                client.jobs.submit(...)

                # Example 3: Get an existing run.
                client.jobs.get_run(...)

                # Example 4: Cancel a run.
                client.jobs.cancel_run(...)

        Returns:
            WorkspaceClient: The authenticated Databricks SDK Workspace Client.
        """
        return self._workspace_client

    def read_file(self, dbfs_path: str, block_size: int = 1024**2) -> bytes:
        """Read a file from DBFS to a **byte string**."""
        if dbfs_path.startswith("dbfs://"):
            dbfs_path = dbfs_path[7:]

        data = b""
        bytes_read = 0
        dbfs_service = self.workspace_client.dbfs

        jdoc = dbfs_service.read(path=dbfs_path, length=block_size)
        data += base64.b64decode(jdoc.data)
        while jdoc.bytes_read == block_size:
            bytes_read += jdoc.bytes_read
            jdoc = dbfs_service.read(path=dbfs_path, offset=bytes_read, length=block_size)
            data += base64.b64decode(jdoc.data)

        return data

    def put_file(
        self, file_obj: IO, dbfs_path: str, overwrite: bool = False, block_size: int = 1024**2
    ) -> None:
        """Upload an arbitrary large file to DBFS.

        This doesn't use the DBFS `Put` API because that endpoint is limited to 1MB.
        """
        if dbfs_path.startswith("dbfs://"):
            dbfs_path = dbfs_path[7:]

        dbfs_service = self.workspace_client.dbfs

        create_response = dbfs_service.create(path=dbfs_path, overwrite=overwrite)
        handle = create_response.handle

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
        run = self.workspace_client.jobs.get_run(databricks_run_id)
        return DatabricksRunState.from_databricks(run.state)

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
            if run_state.is_skipped():
                logger.info(f"Run `{databricks_run_id}` was skipped.")
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
    """Submits jobs created using Dagster config to Databricks, and monitors their progress.

    Attributes:
        host (str): Databricks host, e.g. https://uksouth.azuredatabricks.net.
        token (str): Databricks authentication token.
        poll_interval_sec (float): How often to poll Databricks for run status.
        max_wait_time_sec (int): How long to wait for a run to complete before failing.
    """

    def __init__(
        self,
        host: str,
        token: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        poll_interval_sec: float = 5,
        max_wait_time_sec: int = DEFAULT_RUN_MAX_WAIT_TIME_SEC,
    ):
        self.host = check.str_param(host, "host")
        check.invariant(
            token is None or (oauth_client_id is None and oauth_client_secret is None),
            "Must provide either databricks_token or oauth_credentials, but cannot provide both",
        )
        self.token = check.opt_str_param(token, "token")
        self.oauth_client_id = check.opt_str_param(oauth_client_id, "oauth_client_id")
        self.oauth_client_secret = check.opt_str_param(oauth_client_secret, "oauth_client_secret")
        self.poll_interval_sec = check.numeric_param(poll_interval_sec, "poll_interval_sec")
        self.max_wait_time_sec = check.int_param(max_wait_time_sec, "max_wait_time_sec")

        self._client: DatabricksClient = DatabricksClient(
            host=self.host,
            token=self.token,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
        )

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

            tags = new_cluster.get("custom_tags", {})
            if isinstance(tags, list):
                tags = {x["key"]: x["value"] for x in tags}
            tags["__dagster_version"] = dagster.__version__
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
                        {"pypi": {"package": f"{library_name}=={library.__version__}"}}
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

        return self.client.workspace_client.jobs.submit(
            run_name=run_config.get("run_name"),
            tasks=[
                jobs.SubmitTask.from_dict(
                    {
                        "new_cluster": new_cluster,
                        "existing_cluster_id": existing_cluster_id,
                        # "libraries": [compute.Library.from_dict(lib) for lib in libraries],
                        "libraries": libraries,
                        **task,
                        "task_key": "dagster-task",
                    },
                )
            ],
        ).bind()["run_id"]

    def retrieve_logs_for_run_id(
        self, log: logging.Logger, databricks_run_id: int
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """Retrieve the stdout and stderr logs for a run."""
        run = self.client.workspace_client.jobs.get_run(databricks_run_id)

        # Run.cluster_instance can be None. In that case, fall back to cluster instance on first
        # task. Currently pyspark step launcher runs jobs with singleton tasks.
        cluster_instance = run.cluster_instance or run.tasks[0].cluster_instance
        cluster_id = check.inst(
            cluster_instance.cluster_id,
            str,
            "cluster_id should be string like `1234-123456-abcdefgh` got:"
            f" `{cluster_instance.cluster_id}`",
        )
        cluster = self.client.workspace_client.clusters.get(cluster_id)
        log_config = cluster.cluster_log_conf
        if log_config is None:
            log.warn(
                f"Logs not configured for cluster {cluster_id} used for run {databricks_run_id}"
            )
            return None
        if cast(Optional[compute.S3StorageInfo], log_config.s3) is not None:
            logs_prefix = log_config.s3.destination
            log.warn("Retrieving S3 logs not yet implemented")
            return None
        elif cast(Optional[compute.DbfsStorageInfo], log_config.dbfs) is not None:
            logs_prefix = log_config.dbfs.destination
            stdout = self.wait_for_dbfs_logs(log, logs_prefix, cluster_id, "stdout")
            stderr = self.wait_for_dbfs_logs(log, logs_prefix, cluster_id, "stderr")
            return stdout, stderr

    def wait_for_dbfs_logs(
        self,
        log: logging.Logger,
        prefix: str,
        cluster_id: str,
        filename: str,
        waiter_delay: int = 10,
        waiter_max_attempts: int = 10,
    ) -> Optional[str]:
        """Attempt up to `waiter_max_attempts` attempts to get logs from DBFS."""
        path = "/".join([prefix, cluster_id, "driver", filename])
        log.info(f"Retrieving logs from {path}")
        num_attempts = 0
        while num_attempts <= waiter_max_attempts:
            try:
                logs = self.client.read_file(path)
                return logs.decode("utf-8")
            except requests.exceptions.HTTPError:
                num_attempts += 1
                time.sleep(waiter_delay)
        log.warn("Could not retrieve cluster logs!")
