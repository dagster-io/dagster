import base64
import logging
import os
import time
from collections.abc import Mapping
from enum import Enum
from importlib.metadata import version
from typing import IO, Any, Final, Optional

import dagster
import dagster._check as check
import dagster_pyspark
import requests.exceptions
from dagster._annotations import public
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import (
    Config,
    DefaultCredentials,
    azure_service_principal,
    oauth_service_principal,
    pat_auth,
)
from databricks.sdk.service import jobs

import dagster_databricks
from dagster_databricks.types import DatabricksRunState
from dagster_databricks.version import __version__

# wait at most 24 hours by default for run execution
DEFAULT_RUN_MAX_WAIT_TIME_SEC: Final = 24 * 60 * 60


class DatabricksError(Exception):
    pass


class AuthTypeEnum(Enum):
    OAUTH_M2M = "oauth-m2m"
    PAT = "pat"
    AZURE_CLIENT_SECRET = "azure-client-secret"
    DEFAULT = "default"


class WorkspaceClientFactory:
    def __init__(
        self,
        host: Optional[str],
        token: Optional[str],
        oauth_client_id: Optional[str],
        oauth_client_secret: Optional[str],
        azure_client_id: Optional[str],
        azure_client_secret: Optional[str],
        azure_tenant_id: Optional[str],
    ):
        """Initialize the Databricks Workspace client. Users may provide explicit credentials for a PAT, databricks
        service principal oauth credentials, or azure service principal credentials. If no credentials are provided,
        the underlying WorkspaceClient from `databricks.sdk` will attempt to read credentials from the environment or
        from the `~/.databrickscfg` file. For more information, see the Databricks SDK docs on various ways you can
        authenticate with the WorkspaceClient, through which most interactions with the Databricks API occur.
        <https://docs.databricks.com/en/dev-tools/auth.html#authentication-for-databricks-automation>`_.
        """
        self._raise_if_multiple_auth_types(
            token=token,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            azure_tenant_id=azure_tenant_id,
        )
        self._assert_valid_credentials_combos(
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            azure_tenant_id=azure_tenant_id,
        )
        auth_type = self._get_auth_type(
            token,
            oauth_client_id,
            oauth_client_secret,
            azure_client_id,
            azure_client_secret,
            azure_tenant_id,
        )
        product_info = {"product": "dagster-databricks", "product_version": __version__}

        # Figure out what credentials provider to use based on any explicitly-provided credentials. If none were
        # provided, then fallback to the default credentials provider, which will attempt to read credentials from
        # the environment or from a `~/.databrickscfg` file, if it exists.

        if auth_type == AuthTypeEnum.OAUTH_M2M:
            host = self._resolve_host(host)
            c = Config(
                host=host,
                client_id=oauth_client_id,
                client_secret=oauth_client_secret,
                credentials_provider=oauth_service_principal,
                **product_info,
            )
        elif auth_type == AuthTypeEnum.PAT:
            host = self._resolve_host(host)
            c = Config(host=host, token=token, credentials_provider=pat_auth, **product_info)
        elif auth_type == AuthTypeEnum.AZURE_CLIENT_SECRET:
            host = self._resolve_host(host)
            c = Config(
                host=host,
                azure_client_id=azure_client_id,
                azure_client_secret=azure_client_secret,
                azure_tenant_id=azure_tenant_id,
                credentials_provider=azure_service_principal,
                **product_info,
            )
        elif auth_type == AuthTypeEnum.DEFAULT:
            # Can be used to automatically read credentials from environment or ~/.databrickscfg file. This is common
            # when launching Databricks jobs from a laptop development setting through Dagster
            if host is not None:
                # This allows for explicit override of the host, while letting other credentials be read from the
                # environment or ~/.databrickscfg file
                c = Config(host=host, credentials_provider=DefaultCredentials(), **product_info)  # type: ignore  # (bad stubs)
            else:
                # The initialization machinery in the Config object will look for the host and other auth info in the
                # environment, as long as no values are provided for those attributes (including None)
                c = Config(credentials_provider=DefaultCredentials(), **product_info)  # type: ignore  # (bad stubs)
        else:
            raise ValueError(f"Unexpected auth type {auth_type}")
        self.config = c

    def _raise_if_multiple_auth_types(
        self,
        token: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        azure_client_id: Optional[str] = None,
        azure_client_secret: Optional[str] = None,
        azure_tenant_id: Optional[str] = None,
    ):
        more_than_one_auth_type_provided = (
            sum(
                [
                    True
                    for _ in [
                        token,
                        (oauth_client_id and oauth_client_secret),
                        (azure_client_id and azure_client_secret and azure_tenant_id),
                    ]
                    if _
                ]
            )
            > 1
        )
        if more_than_one_auth_type_provided:
            raise ValueError(
                "Can only provide one of token, oauth credentials, or azure credentials"
            )

    @staticmethod
    def _get_auth_type(
        token: Optional[str],
        oauth_client_id: Optional[str],
        oauth_client_secret: Optional[str],
        azure_client_id: Optional[str],
        azure_client_secret: Optional[str],
        azure_tenant_id: Optional[str],
    ) -> AuthTypeEnum:
        """Get the type of authentication used to initialize the WorkspaceClient."""
        if oauth_client_id and oauth_client_secret:
            auth_type = AuthTypeEnum.OAUTH_M2M
        elif token:
            auth_type = AuthTypeEnum.PAT
        elif azure_client_id and azure_client_secret and azure_tenant_id:
            auth_type = AuthTypeEnum.AZURE_CLIENT_SECRET
        else:
            auth_type = AuthTypeEnum.DEFAULT
        return auth_type

    @staticmethod
    def _assert_valid_credentials_combos(
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        azure_client_id: Optional[str] = None,
        azure_client_secret: Optional[str] = None,
        azure_tenant_id: Optional[str] = None,
    ):
        """Ensure that all required credentials are provided for the given auth type."""
        if (oauth_client_id and not oauth_client_secret) or (
            oauth_client_secret and not oauth_client_id
        ):
            raise ValueError(
                "If using databricks service principal oauth credentials, both oauth_client_id and"
                " oauth_client_secret must be provided"
            )
        if (
            (azure_client_id and not azure_client_secret and not azure_tenant_id)
            or (azure_client_secret and not azure_client_id and not azure_tenant_id)
            or (azure_tenant_id and not azure_client_id and not azure_client_secret)
        ):
            raise ValueError(
                "If using azure service principal auth, azure_client_id, azure_client_secret, and"
                " azure_tenant_id must be provided"
            )

    def get_workspace_client(self) -> WorkspaceClient:
        return WorkspaceClient(config=self.config)

    @staticmethod
    def _resolve_host(host: Optional[str]) -> str:
        host = host if host else os.getenv("DATABRICKS_HOST")
        if host is None:
            raise ValueError(
                "Must provide host explicitly or in DATABRICKS_HOST env var when providing"
                " credentials explicitly"
            )
        return host


class DatabricksClient:
    """A thin wrapper over the Databricks REST API."""

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        azure_client_id: Optional[str] = None,
        azure_client_secret: Optional[str] = None,
        azure_tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        self.host = host
        self.workspace_id = workspace_id

        workspace_client_factory = WorkspaceClientFactory(
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            azure_tenant_id=azure_tenant_id,
            token=token,
            host=host,
        )
        self._workspace_client = workspace_client_factory.get_workspace_client()

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
        jdoc_data = check.not_none(jdoc.data, f"read file {dbfs_path} with no data")
        data += base64.b64decode(jdoc_data)
        while jdoc.bytes_read == block_size:
            bytes_read += check.not_none(jdoc.bytes_read)
            jdoc = dbfs_service.read(path=dbfs_path, offset=bytes_read, length=block_size)
            jdoc_data = check.not_none(jdoc.data, f"read file {dbfs_path} with no data")
            data += base64.b64decode(jdoc_data)

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
        handle = check.not_none(
            create_response.handle, "create file response did not return handle"
        )

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
        if run.state is None:
            check.failed("Databricks job run state is None")
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
        max_wait_time_sec: float,
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

    Args:
        host (str): Databricks host, e.g. https://uksouth.azuredatabricks.net.
        token (str): Databricks authentication token.
        poll_interval_sec (float): How often to poll Databricks for run status.
        max_wait_time_sec (int): How long to wait for a run to complete before failing.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        oauth_client_id: Optional[str] = None,
        oauth_client_secret: Optional[str] = None,
        azure_client_id: Optional[str] = None,
        azure_client_secret: Optional[str] = None,
        azure_tenant_id: Optional[str] = None,
        poll_interval_sec: float = 5,
        max_wait_time_sec: float = DEFAULT_RUN_MAX_WAIT_TIME_SEC,
    ):
        self.host = check.opt_str_param(host, "host")
        self.token = check.opt_str_param(token, "token")
        self.poll_interval_sec = check.numeric_param(poll_interval_sec, "poll_interval_sec")
        self.max_wait_time_sec = check.int_param(max_wait_time_sec, "max_wait_time_sec")

        oauth_client_id = check.opt_str_param(oauth_client_id, "oauth_client_id")
        oauth_client_secret = check.opt_str_param(oauth_client_secret, "oauth_client_secret")
        azure_client_id = check.opt_str_param(azure_client_id, "azure_client_id")
        azure_client_secret = check.opt_str_param(azure_client_secret, "azure_client_secret")
        azure_tenant_id = check.opt_str_param(azure_tenant_id, "azure_tenant_id")

        self._client: DatabricksClient = DatabricksClient(
            host=self.host,
            token=self.token,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
            azure_tenant_id=azure_tenant_id,
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

            if "driver_instance_pool_id" in nodes:
                check.invariant(
                    "instance_pool_id" in nodes,
                    "Usage of `driver_instance_pool_id` requires that `instance_pool_id` be specified"
                    " for worker nodes",
                )

            if "instance_pool_id" in nodes:
                new_cluster["instance_pool_id"] = nodes["instance_pool_id"]

                if "driver_instance_pool_id" in nodes:
                    new_cluster["driver_instance_pool_id"] = nodes["driver_instance_pool_id"]
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

            if "databricks-sdk" not in python_libraries:
                libraries.append(
                    {"pypi": {"package": f"databricks-sdk=={version('databricks-sdk')}"}}
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
                        "libraries": libraries,
                        **task,
                        "task_key": "dagster-task",
                    },
                )
            ],
            idempotency_token=run_config.get("idempotency_token"),
            timeout_seconds=run_config.get("timeout_seconds"),
            health=jobs.JobsHealthRules.from_dict({"rules": run_config["job_health_settings"]})
            if "job_health_settings" in run_config
            else None,
            email_notifications=jobs.JobEmailNotifications.from_dict(
                run_config["email_notifications"]
            )
            if "email_notifications" in run_config
            else None,
            notification_settings=jobs.JobNotificationSettings.from_dict(
                run_config["notification_settings"]
            )
            if "notification_settings" in run_config
            else None,
            webhook_notifications=jobs.WebhookNotifications.from_dict(
                run_config["webhook_notifications"]
            )
            if "webhook_notifications" in run_config
            else None,
        ).bind()["run_id"]

    def retrieve_logs_for_run_id(
        self, log: logging.Logger, databricks_run_id: int
    ) -> Optional[tuple[Optional[str], Optional[str]]]:
        """Retrieve the stdout and stderr logs for a run."""
        run = self.client.workspace_client.jobs.get_run(databricks_run_id)
        # Run.cluster_instance can be None. In that case, fall back to cluster instance on first
        # task. Currently pyspark step launcher runs jobs with singleton tasks.
        cluster_instance = check.not_none(
            run.cluster_instance or check.not_none(run.tasks)[0].cluster_instance,
            "Run has no attached cluster instance.",
        )
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
        if log_config.s3 is not None:
            logs_prefix = check.not_none(
                log_config.s3.destination, "S3 logs destination not set for cluster"
            )
            log.warn("Retrieving S3 logs not yet implemented")
            return None
        elif log_config.dbfs is not None:
            logs_prefix = check.not_none(
                log_config.dbfs.destination, "DBFS logs destination not set for cluster"
            )
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
