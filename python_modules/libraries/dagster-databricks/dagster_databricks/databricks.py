import base64
import time

import requests.exceptions
from databricks_api import DatabricksAPI

import dagster
import dagster._check as check

from .types import (
    DATABRICKS_RUN_TERMINATED_STATES,
    DatabricksRunLifeCycleState,
    DatabricksRunResultState,
)

# wait at most 24 hours by default for run execution
DEFAULT_RUN_MAX_WAIT_TIME_SEC = 24 * 60 * 60


class DatabricksError(Exception):
    pass


class DatabricksClient:
    """A thin wrapper over the Databricks REST API."""

    def __init__(self, host, token, workspace_id=None):
        self.host = host
        self.workspace_id = workspace_id
        self.client = DatabricksAPI(host=host, token=token)

    def submit_run(self, *args, **kwargs):
        """Submit a run directly to the 'Runs Submit' API."""
        return self.client.jobs.submit_run(*args, **kwargs)["run_id"]  # pylint: disable=no-member

    def read_file(self, dbfs_path, block_size=1024**2):
        """Read a file from DBFS to a **byte string**."""

        if dbfs_path.startswith("dbfs://"):
            dbfs_path = dbfs_path[7:]
        data = b""
        bytes_read = 0
        jdoc = self.client.dbfs.read(path=dbfs_path, length=block_size)  # pylint: disable=no-member
        data += base64.b64decode(jdoc["data"])
        while jdoc["bytes_read"] == block_size:
            bytes_read += jdoc["bytes_read"]
            jdoc = self.client.dbfs.read(  # pylint: disable=no-member
                path=dbfs_path, offset=bytes_read, length=block_size
            )
            data += base64.b64decode(jdoc["data"])
        return data

    def put_file(self, file_obj, dbfs_path, overwrite=False, block_size=1024**2):
        """Upload an arbitrary large file to DBFS.

        This doesn't use the DBFS `Put` API because that endpoint is limited to 1MB.
        """
        if dbfs_path.startswith("dbfs://"):
            dbfs_path = dbfs_path[7:]
        create_response = self.client.dbfs.create(  # pylint: disable=no-member
            path=dbfs_path, overwrite=overwrite
        )
        handle = create_response["handle"]

        block = file_obj.read(block_size)
        while block:
            data = base64.b64encode(block).decode("utf-8")
            self.client.dbfs.add_block(data=data, handle=handle)  # pylint: disable=no-member
            block = file_obj.read(block_size)

        self.client.dbfs.close(handle=handle)  # pylint: disable=no-member

    def get_run_state(self, databricks_run_id):
        """Get the state of a run by Databricks run ID (_not_ dagster run ID).

        Return a `DatabricksRunState` object. Note that the `result_state`
        attribute may be `None` if the run hasn't yet terminated.
        """
        run = self.client.jobs.get_run(databricks_run_id)  # pylint: disable=no-member
        state = run["state"]
        result_state = state.get("result_state")
        if result_state:
            result_state = DatabricksRunResultState(result_state)
        return DatabricksRunState(
            life_cycle_state=DatabricksRunLifeCycleState(state["life_cycle_state"]),
            result_state=result_state,
            state_message=state["state_message"],
        )


class DatabricksRunState:
    """Represents the state of a Databricks job run."""

    def __init__(self, life_cycle_state, result_state, state_message):
        self.life_cycle_state = life_cycle_state
        self.result_state = result_state
        self.state_message = state_message

    def has_terminated(self):
        """Has the job terminated?"""
        return self.life_cycle_state in DATABRICKS_RUN_TERMINATED_STATES

    def is_successful(self):
        """Was the job successful?"""
        return self.result_state == DatabricksRunResultState.Success

    def __repr__(self):
        return str(self.__dict__)


class DatabricksJobRunner:
    """Submits jobs created using Dagster config to Databricks, and monitors their progress."""

    def __init__(
        self, host, token, poll_interval_sec=5, max_wait_time_sec=DEFAULT_RUN_MAX_WAIT_TIME_SEC
    ):
        """Args:
        host (str): Databricks host, e.g. https://uksouth.azuredatabricks.net
        token (str): Databricks token
        """
        self.host = check.str_param(host, "host")
        self.token = check.str_param(token, "token")
        self.poll_interval_sec = check.numeric_param(poll_interval_sec, "poll_interval_sec")
        self.max_wait_time_sec = check.int_param(max_wait_time_sec, "max_wait_time_sec")

        self._client = DatabricksClient(host=self.host, token=self.token)

    @property
    def client(self):
        """Return the underlying `DatabricksClient` object."""
        return self._client

    def submit_run(self, run_config, task):
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
        python_libraries = {
            x["pypi"]["package"].split("==")[0].replace("_", "-") for x in libraries if "pypi" in x
        }
        for library in ["dagster", "dagster-databricks", "dagster-pyspark"]:
            if library not in python_libraries:
                libraries.append(
                    {"pypi": {"package": "{}=={}".format(library, dagster.__version__)}}
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

        config = dict(
            run_name=run_config.get("run_name"),
            new_cluster=new_cluster,
            existing_cluster_id=existing_cluster_id,
            libraries=libraries,
            **task,
        )
        return self.client.submit_run(**config)

    def retrieve_logs_for_run_id(self, log, databricks_run_id):
        """Retrieve the stdout and stderr logs for a run."""
        api_client = self.client.client
        run = api_client.jobs.get_run(databricks_run_id)  # pylint: disable=no-member
        cluster = api_client.cluster.get_cluster(  # pylint: disable=no-member
            run["cluster_instance"]["cluster_id"]
        )
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
        self, log, prefix, cluster_id, filename, waiter_delay=10, waiter_max_attempts=10
    ):
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

    def wait_for_run_to_complete(self, log, databricks_run_id):
        return wait_for_run_to_complete(
            self.client, log, databricks_run_id, self.poll_interval_sec, self.max_wait_time_sec
        )


def poll_run_state(
    client,
    log,
    start_poll_time: float,
    databricks_run_id: int,
    max_wait_time_sec: float,
):
    run_state = client.get_run_state(databricks_run_id)
    if run_state.has_terminated():
        if run_state.is_successful():
            log.info("Run %s completed successfully" % databricks_run_id)
            return True
        else:
            error_message = "Run %s failed with result state: %s. Message: %s" % (
                databricks_run_id,
                run_state.result_state,
                run_state.state_message,
            )
            log.error(error_message)
            raise DatabricksError(error_message)
    else:
        log.info("Run %s in state %s" % (databricks_run_id, run_state))
    if time.time() - start_poll_time > max_wait_time_sec:
        raise DatabricksError(
            "Job run {} took more than {}s to complete; failing".format(
                databricks_run_id, max_wait_time_sec
            )
        )
    return False


def wait_for_run_to_complete(client, log, databricks_run_id, poll_interval_sec, max_wait_time_sec):
    """Wait for a Databricks run to complete."""
    check.int_param(databricks_run_id, "databricks_run_id")
    log.info("Waiting for Databricks run %s to complete..." % databricks_run_id)
    start = time.time()
    while True:
        if poll_run_state(client, log, start, databricks_run_id, max_wait_time_sec):
            return
        time.sleep(poll_interval_sec)
