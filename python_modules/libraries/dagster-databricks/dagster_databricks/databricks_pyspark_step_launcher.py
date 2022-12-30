import gzip
import io
import os.path
import pickle
import tempfile
import time
import zlib

from dagster_databricks import databricks_step_main
from dagster_databricks.databricks import (
    DEFAULT_RUN_MAX_WAIT_TIME_SEC,
    DatabricksJobRunner,
    poll_run_state,
)
from dagster_pyspark.utils import build_pyspark_zip
from requests import HTTPError

from dagster import Bool, Field, IntSource, StringSource
from dagster import _check as check
from dagster import resource
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.errors import raise_execution_interrupts
from dagster._core.execution.plan.external_step import (
    PICKLED_EVENTS_FILE_NAME,
    PICKLED_STEP_RUN_REF_FILE_NAME,
    step_context_to_step_run_ref,
)
from dagster._serdes import deserialize_value
from dagster._utils.backoff import backoff

from .configs import (
    define_databricks_env_variables,
    define_databricks_permissions,
    define_databricks_secrets_config,
    define_databricks_storage_config,
    define_databricks_submit_run_config,
)

CODE_ZIP_NAME = "code.zip"
PICKLED_CONFIG_FILE_NAME = "config.pkl"
DAGSTER_SYSTEM_ENV_VARS = {
    "DAGSTER_CLOUD_DEPLOYMENT_NAME",
    "DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT",
    "DAGSTER_CLOUD_GIT_SHA",
    "DAGSTER_CLOUD_GIT_TIMESTAMP",
    "DAGSTER_CLOUD_GIT_AUTHOR_EMAIL",
    "DAGSTER_CLOUD_GIT_AUTHOR_NAME",
    "DAGSTER_CLOUD_GIT_MESSAGE",
    "DAGSTER_CLOUD_GIT_BRANCH",
    "DAGSTER_CLOUD_GIT_REPO",
    "DAGSTER_CLOUD_PULL_REQUEST_ID",
    "DAGSTER_CLOUD_PULL_REQUEST_STATUS",
}


@resource(
    {
        "run_config": define_databricks_submit_run_config(),
        "permissions": define_databricks_permissions(),
        "databricks_host": Field(
            StringSource,
            is_required=True,
            description="Databricks host, e.g. uksouth.azuredatabricks.com",
        ),
        "databricks_token": Field(
            StringSource,
            is_required=True,
            description="Databricks access token",
        ),
        "env_variables": define_databricks_env_variables(),
        "secrets_to_env_variables": define_databricks_secrets_config(),
        "storage": define_databricks_storage_config(),
        "local_pipeline_package_path": Field(
            StringSource,
            is_required=False,
            description="Absolute path to root python package containing your Dagster code. If you "
            "set this value to a directory lower than the root package, and have user relative "
            "imports in your code (e.g. `from .foo import bar`), it's likely you'll encounter an "
            "import error on the remote step. Before every step run, the launcher will zip up the "
            "code in this local path, upload it to DBFS, and unzip it into the Python path of the "
            "remote Spark process. This gives the remote process access to up-to-date user code.",
        ),
        "local_dagster_job_package_path": Field(
            StringSource,
            is_required=False,
            description="Absolute path to root python package containing your Dagster code. If you "
            "set this value to a directory lower than the root package, and have user relative "
            "imports in your code (e.g. `from .foo import bar`), it's likely you'll encounter an "
            "import error on the remote step. Before every step run, the launcher will zip up the "
            "code in this local path, upload it to DBFS, and unzip it into the Python path of the "
            "remote Spark process. This gives the remote process access to up-to-date user code.",
        ),
        "staging_prefix": Field(
            StringSource,
            is_required=False,
            default_value="/dagster_staging",
            description="Directory in DBFS to use for uploaded job code. Must be absolute.",
        ),
        "wait_for_logs": Field(
            Bool,
            is_required=False,
            default_value=False,
            description="If set, and if the specified cluster is configured to export logs, "
            "the system will wait after job completion for the logs to appear in the configured "
            "location. Note that logs are copied every 5 minutes, so enabling this will add "
            "several minutes to the job runtime. NOTE: this integration will export stdout/stderr"
            "from the remote Databricks process automatically, so this option is not generally "
            "necessary.",
        ),
        "max_completion_wait_time_seconds": Field(
            IntSource,
            is_required=False,
            default_value=DEFAULT_RUN_MAX_WAIT_TIME_SEC,
            description="If the Databricks job run takes more than this many seconds, then "
            "consider it failed and terminate the step.",
        ),
        "poll_interval_sec": Field(
            float,
            is_required=False,
            default_value=5.0,
            description="How frequently Dagster will poll Databricks to determine the state of the job.",
        ),
        "verbose_logs": Field(
            bool,
            default_value=True,
            description="Determines whether to display debug logs emitted while job is being polled. "
            "It can be helpful for Dagit performance to set to False when running long-running or fan-out "
            "Databricks jobs, to avoid forcing the UI to fetch large amounts of debug logs.",
        ),
        "add_dagster_env_variables": Field(
            bool,
            default_value=True,
            description="Automatically add Dagster system environment variables. This option is only applicable when "
            "the code being executed is deployed on Dagster Cloud. It will be ignored when the environment "
            "variables provided by Dagster Cloud are not present.",
        ),
    }
)
def databricks_pyspark_step_launcher(context):
    """Resource for running ops as a Databricks Job.

    When this resource is used, the op will be executed in Databricks using the 'Run Submit'
    API. Pipeline code will be zipped up and copied to a directory in DBFS along with the op's
    execution context.

    Use the 'run_config' configuration to specify the details of the Databricks cluster used, and
    the 'storage' key to configure persistent storage on that cluster. Storage is accessed by
    setting the credentials in the Spark context, as documented `here for S3`_ and `here for ADLS`_.

    .. _`here for S3`: https://docs.databricks.com/data/data-sources/aws/amazon-s3.html#alternative-1-set-aws-keys-in-the-spark-context
    .. _`here for ADLS`: https://docs.microsoft.com/en-gb/azure/databricks/data/data-sources/azure/azure-datalake-gen2#--access-directly-using-the-storage-account-access-key
    """
    return DatabricksPySparkStepLauncher(**context.resource_config)


class DatabricksPySparkStepLauncher(StepLauncher):
    def __init__(
        self,
        run_config,
        permissions,
        databricks_host,
        databricks_token,
        secrets_to_env_variables,
        staging_prefix,
        wait_for_logs,
        max_completion_wait_time_seconds,
        env_variables=None,
        storage=None,
        poll_interval_sec=5,
        local_pipeline_package_path=None,
        local_dagster_job_package_path=None,
        verbose_logs=True,
        add_dagster_env_variables=True,
    ):
        self.run_config = check.dict_param(run_config, "run_config")
        self.permissions = check.dict_param(permissions, "permissions")
        self.databricks_host = check.str_param(databricks_host, "databricks_host")
        self.databricks_token = check.str_param(databricks_token, "databricks_token")
        self.secrets = check.list_param(secrets_to_env_variables, "secrets_to_env_variables", dict)
        self.env_variables = check.opt_dict_param(env_variables, "env_variables")
        self.storage = check.opt_dict_param(storage, "storage")
        check.invariant(
            local_dagster_job_package_path is not None or local_pipeline_package_path is not None,
            "Missing config: need to provide either 'local_dagster_job_package_path' or 'local_pipeline_package_path' config entry",
        )
        check.invariant(
            local_dagster_job_package_path is None or local_pipeline_package_path is None,
            "Error in config: Provided both 'local_dagster_job_package_path' and 'local_pipeline_package_path' entries. Need to specify one or the other.",
        )
        self.local_dagster_job_package_path = check.str_param(
            local_pipeline_package_path or local_dagster_job_package_path,
            "local_dagster_job_package_path",
        )
        self.staging_prefix = check.str_param(staging_prefix, "staging_prefix")
        check.invariant(staging_prefix.startswith("/"), "staging_prefix must be an absolute path")
        self.wait_for_logs = check.bool_param(wait_for_logs, "wait_for_logs")

        self.databricks_runner = DatabricksJobRunner(
            host=databricks_host,
            token=databricks_token,
            poll_interval_sec=poll_interval_sec,
            max_wait_time_sec=max_completion_wait_time_seconds,
        )
        self.verbose_logs = check.bool_param(verbose_logs, "verbose_logs")
        self.add_dagster_env_variables = check.bool_param(
            add_dagster_env_variables, "add_dagster_env_variables"
        )

    def launch_step(self, step_context):
        step_run_ref = step_context_to_step_run_ref(
            step_context, self.local_dagster_job_package_path
        )
        run_id = step_context.pipeline_run.run_id
        log = step_context.log

        step_key = step_run_ref.step_key
        self._upload_artifacts(log, step_run_ref, run_id, step_key)

        task = self._get_databricks_task(run_id, step_key)
        databricks_run_id = self.databricks_runner.submit_run(self.run_config, task)

        if self.permissions:
            self._grant_permissions(log, databricks_run_id)

        try:
            # If this is being called within a `capture_interrupts` context, allow interrupts while
            # waiting for the  execution to complete, so that we can terminate slow or hanging steps
            with raise_execution_interrupts():
                yield from self.step_events_iterator(step_context, step_key, databricks_run_id)
        finally:
            self.log_compute_logs(log, run_id, step_key)
            # this is somewhat obsolete
            if self.wait_for_logs:
                self._log_logs_from_cluster(log, databricks_run_id)

    def log_compute_logs(self, log, run_id, step_key):
        try:
            stdout = self.databricks_runner.client.read_file(
                self._dbfs_path(run_id, step_key, "stdout")
            ).decode()
            log.info(f"Captured stdout for step {step_key}:")
            log.info(stdout)
        except Exception as e:
            log.error(
                f"Encountered exception {e} when attempting to load stdout logs for step {step_key}. "
                "Check the databricks console for more info."
            )
        try:
            stderr = self.databricks_runner.client.read_file(
                self._dbfs_path(run_id, step_key, "stderr")
            ).decode()
            log.info(f"Captured stderr for step {step_key}:")
            log.info(stderr)
        except Exception as e:
            log.error(
                f"Encountered exception {e} when attempting to load stderr logs for step {step_key}. "
                "Check the databricks console for more info."
            )

    def step_events_iterator(self, step_context, step_key: str, databricks_run_id: int):
        """The launched Databricks job writes all event records to a specific dbfs file. This iterator
        regularly reads the contents of the file, adds any events that have not yet been seen to
        the instance, and yields any DagsterEvents.

        By doing this, we simulate having the remote Databricks process able to directly write to
        the local DagsterInstance. Importantly, this means that timestamps (and all other record
        properties) will be sourced from the Databricks process, rather than recording when this
        process happens to log them.
        """

        check.int_param(databricks_run_id, "databricks_run_id")
        processed_events = 0
        start = time.time()
        done = False
        step_context.log.info("Waiting for Databricks run %s to complete..." % databricks_run_id)
        while not done:
            with raise_execution_interrupts():
                if self.verbose_logs:
                    step_context.log.debug(
                        "Waiting %.1f seconds...", self.databricks_runner.poll_interval_sec
                    )
                time.sleep(self.databricks_runner.poll_interval_sec)
                try:
                    done = poll_run_state(
                        self.databricks_runner.client,
                        step_context.log,
                        start,
                        databricks_run_id,
                        self.databricks_runner.max_wait_time_sec,
                        verbose_logs=self.verbose_logs,
                    )
                finally:
                    all_events = self.get_step_events(
                        step_context.run_id, step_key, step_context.previous_attempt_count
                    )
                    # we get all available records on each poll, but we only want to process the
                    # ones we haven't seen before
                    for event in all_events[processed_events:]:
                        # write each event from the DataBricks instance to the local instance
                        step_context.instance.handle_new_event(event)
                        if event.is_dagster_event:
                            yield event.dagster_event
                    processed_events = len(all_events)

        step_context.log.info(f"Databricks run {databricks_run_id} completed.")

    def get_step_events(self, run_id: str, step_key: str, retry_number: int):
        path = self._dbfs_path(run_id, step_key, f"{retry_number}_{PICKLED_EVENTS_FILE_NAME}")

        def _get_step_records():
            serialized_records = self.databricks_runner.client.read_file(path)
            if not serialized_records:
                return []
            return deserialize_value(pickle.loads(gzip.decompress(serialized_records)))

        try:
            # reading from dbfs while it writes can be flaky
            # allow for retry if we get malformed data
            return backoff(
                fn=_get_step_records,
                retry_on=(pickle.UnpicklingError, gzip.BadGzipFile, zlib.error, EOFError),
                max_retries=4,
            )
        # if you poll before the Databricks process has had a chance to create the file,
        # we expect to get this error
        except HTTPError as e:
            if e.response.json().get("error_code") == "RESOURCE_DOES_NOT_EXIST":
                return []

        return []

    def _grant_permissions(self, log, databricks_run_id, request_retries=3):
        api_client = self.databricks_runner.client.client.client

        # Retrieve run info
        cluster_id = None
        for i in range(1, request_retries + 1):
            run_info = self.databricks_runner.client.get_run(databricks_run_id)
            # if a new job cluster is created, the cluster_instance key may not be immediately present in the run response
            try:
                cluster_id = run_info["cluster_instance"]["cluster_id"]
                break
            except:
                log.warning(
                    f"Failed to retrieve cluster info for databricks_run_id {databricks_run_id}. "
                    f"Retrying {i} of {request_retries} times."
                )
                time.sleep(5)
        if not cluster_id:
            log.warning(
                f"Failed to retrieve cluster info for databricks_run_id {databricks_run_id} "
                f"{request_retries} times. Skipping permission updates..."
            )
            return

        # Update job permissions
        if "job_permissions" in self.permissions:
            job_permissions = self._format_permissions(self.permissions["job_permissions"])
            job_id = run_info["job_id"]
            log.debug(f"Updating job permissions with following json: {job_permissions}")
            response = api_client.perform_query(
                method="PATCH", path=f"/permissions/jobs/{job_id}", data=job_permissions
            )
            log.info(f"Successfully updated cluster permissions | Response: {response}")

        # Update cluster permissions
        if "cluster_permissions" in self.permissions:
            if "existing" in self.run_config["cluster"]:
                raise ValueError(
                    "Attempting to update permissions of an existing cluster. "
                    "This is dangerous and thus unsupported."
                )
            cluster_permissions = self._format_permissions(self.permissions["cluster_permissions"])
            log.debug(f"Updating cluster permissions with following json: {cluster_permissions}")
            response = api_client.perform_query(
                method="PATCH",
                path=f"/permissions/clusters/{cluster_id}",
                data=cluster_permissions,
            )
            log.info(f"Successfully updated cluster permissions | Response: {response}")

    def _format_permissions(self, input_permissions):
        permissions = {"access_control_list": []}
        for permission_level, accessors in input_permissions.items():
            for accessor in accessors:
                permissions["access_control_list"].append(
                    {**accessor, **{"permission_level": permission_level}}
                )
        return permissions

    def _get_databricks_task(self, run_id, step_key):
        """Construct the 'task' parameter to  be submitted to the Databricks API.

        This will create a 'spark_python_task' dict where `python_file` is a path on DBFS
        pointing to the 'databricks_step_main.py' file, and `parameters` is an array with a single
        element, a path on DBFS pointing to the picked `step_run_ref` data.

        See https://docs.databricks.com/dev-tools/api/latest/jobs.html#jobssparkpythontask.
        """
        python_file = self._dbfs_path(run_id, step_key, self._main_file_name())
        parameters = [
            self._internal_dbfs_path(run_id, step_key, PICKLED_STEP_RUN_REF_FILE_NAME),
            self._internal_dbfs_path(run_id, step_key, PICKLED_CONFIG_FILE_NAME),
            self._internal_dbfs_path(run_id, step_key, CODE_ZIP_NAME),
        ]
        return {"spark_python_task": {"python_file": python_file, "parameters": parameters}}

    def _upload_artifacts(self, log, step_run_ref, run_id, step_key):
        """Upload the step run ref and pyspark code to DBFS to run as a job."""

        log.info("Uploading main file to DBFS")
        main_local_path = self._main_file_local_path()
        with open(main_local_path, "rb") as infile:
            self.databricks_runner.client.put_file(
                infile, self._dbfs_path(run_id, step_key, self._main_file_name()), overwrite=True
            )

        log.info("Uploading dagster job to DBFS")
        with tempfile.TemporaryDirectory() as temp_dir:
            # Zip and upload package containing dagster job
            zip_local_path = os.path.join(temp_dir, CODE_ZIP_NAME)
            build_pyspark_zip(zip_local_path, self.local_dagster_job_package_path)
            with open(zip_local_path, "rb") as infile:
                self.databricks_runner.client.put_file(
                    infile, self._dbfs_path(run_id, step_key, CODE_ZIP_NAME), overwrite=True
                )

        log.info("Uploading step run ref file to DBFS")
        step_pickle_file = io.BytesIO()

        pickle.dump(step_run_ref, step_pickle_file)
        step_pickle_file.seek(0)
        self.databricks_runner.client.put_file(
            step_pickle_file,
            self._dbfs_path(run_id, step_key, PICKLED_STEP_RUN_REF_FILE_NAME),
            overwrite=True,
        )

        databricks_config = self.create_remote_config()
        log.info("Uploading Databricks configuration to DBFS")
        databricks_config_file = io.BytesIO()
        pickle.dump(databricks_config, databricks_config_file)
        databricks_config_file.seek(0)
        self.databricks_runner.client.put_file(
            databricks_config_file,
            self._dbfs_path(run_id, step_key, PICKLED_CONFIG_FILE_NAME),
            overwrite=True,
        )

    def get_dagster_env_variables(self):
        out = {}
        if self.add_dagster_env_variables:
            for var in DAGSTER_SYSTEM_ENV_VARS:
                if os.getenv(var):
                    out.update({var: os.getenv(var)})
        return out

    def create_remote_config(self):
        env_variables = self.get_dagster_env_variables()
        env_variables.update(self.env_variables)
        databricks_config = DatabricksConfig(
            env_variables=env_variables,
            storage=self.storage,
            secrets=self.secrets,
        )
        return databricks_config

    def _log_logs_from_cluster(self, log, run_id):
        logs = self.databricks_runner.retrieve_logs_for_run_id(log, run_id)
        if logs is None:
            return
        stdout, stderr = logs
        if stderr:
            log.info(stderr)
        if stdout:
            log.info(stdout)

    def _main_file_name(self):
        return os.path.basename(self._main_file_local_path())

    def _main_file_local_path(self):
        return databricks_step_main.__file__

    def _sanitize_step_key(self, step_key: str) -> str:
        # step_keys of dynamic steps contain brackets, which are invalid characters
        return step_key.replace("[", "__").replace("]", "__")

    def _dbfs_path(self, run_id, step_key, filename):
        path = "/".join(
            [
                self.staging_prefix,
                run_id,
                self._sanitize_step_key(step_key),
                os.path.basename(filename),
            ]
        )
        return "dbfs://{}".format(path)

    def _internal_dbfs_path(self, run_id, step_key, filename):
        """Scripts running on Databricks should access DBFS at /dbfs/."""
        path = "/".join(
            [
                self.staging_prefix,
                run_id,
                self._sanitize_step_key(step_key),
                os.path.basename(filename),
            ]
        )
        return "/dbfs/{}".format(path)


class DatabricksConfig:
    """Represents configuration required by Databricks to run jobs.

    Instances of this class will be created when a Databricks step is launched and will contain
    all configuration and secrets required to set up storage and environment variables within
    the Databricks environment. The instance will be serialized and uploaded to Databricks
    by the step launcher, then deserialized as part of the 'main' script when the job is running
    in Databricks.

    The `setup` method handles the actual setup prior to op execution on the Databricks side.

    This config is separated out from the regular Dagster run config system because the setup
    is done by the 'main' script before entering a Dagster context (i.e. using `run_step_from_ref`).
    We use a separate class to avoid coupling the setup to the format of the `step_run_ref` object.
    """

    def __init__(self, env_variables, storage, secrets):
        """Create a new DatabricksConfig object.

        `storage` and `secrets` should be of the same shape as the `storage` and
        `secrets_to_env_variables` config passed to `databricks_pyspark_step_launcher`.
        """
        self.env_variables = env_variables
        self.storage = storage
        self.secrets = secrets

    def setup(self, dbutils, sc):
        """Set up storage and environment variables on Databricks.

        The `dbutils` and `sc` arguments must be passed in by the 'main' script, as they
        aren't accessible by any other modules.
        """
        self.setup_storage(dbutils, sc)
        self.setup_environment(dbutils)

    def setup_storage(self, dbutils, sc):
        """Set up storage using either S3 or ADLS2."""
        if "s3" in self.storage:
            self.setup_s3_storage(self.storage["s3"], dbutils, sc)
        elif "adls2" in self.storage:
            self.setup_adls2_storage(self.storage["adls2"], dbutils, sc)

    def setup_s3_storage(self, s3_storage, dbutils, sc):
        """Obtain AWS credentials from Databricks secrets and export so both Spark and boto can use them."""

        scope = s3_storage["secret_scope"]

        access_key = dbutils.secrets.get(scope=scope, key=s3_storage["access_key_key"])
        secret_key = dbutils.secrets.get(scope=scope, key=s3_storage["secret_key_key"])

        # Spark APIs will use this.
        # See https://docs.databricks.com/data/data-sources/aws/amazon-s3.html#alternative-1-set-aws-keys-in-the-spark-context.
        sc._jsc.hadoopConfiguration().set(  # pylint: disable=protected-access
            "fs.s3n.awsAccessKeyId", access_key
        )
        sc._jsc.hadoopConfiguration().set(  # pylint: disable=protected-access
            "fs.s3n.awsSecretAccessKey", secret_key
        )

        # Boto will use these.
        os.environ["AWS_ACCESS_KEY_ID"] = access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key

    def setup_adls2_storage(self, adls2_storage, dbutils, sc):
        """Obtain an Azure Storage Account key from Databricks secrets and export so Spark can use it."""
        storage_account_key = dbutils.secrets.get(
            scope=adls2_storage["secret_scope"], key=adls2_storage["storage_account_key_key"]
        )
        # Spark APIs will use this.
        # See https://docs.microsoft.com/en-gb/azure/databricks/data/data-sources/azure/azure-datalake-gen2#--access-directly-using-the-storage-account-access-key
        # sc is globally defined in the Databricks runtime and points to the Spark context
        sc._jsc.hadoopConfiguration().set(  # pylint: disable=protected-access
            "fs.azure.account.key.{}.dfs.core.windows.net".format(
                adls2_storage["storage_account_name"]
            ),
            storage_account_key,
        )

    def setup_environment(self, dbutils):
        """Setup any environment variables required by the run.

        Extract any secrets in the run config and export them as environment variables.

        This is important for any `StringSource` config since the environment variables
        won't ordinarily be available in the Databricks execution environment.
        """
        for env_k, env_v in self.env_variables.items():
            os.environ[env_k] = env_v

        for secret in self.secrets:
            name = secret["name"]
            key = secret["key"]
            scope = secret["scope"]
            print(  # pylint: disable=print-call
                "Exporting {} from Databricks secret {}, scope {}".format(name, key, scope)
            )
            val = dbutils.secrets.get(scope=scope, key=key)
            os.environ[name] = val
