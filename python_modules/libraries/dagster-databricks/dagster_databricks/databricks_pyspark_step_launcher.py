import io
import os.path
import pickle

from dagster_databricks import DatabricksJobRunner, databricks_step_main
from dagster_pyspark.utils import build_pyspark_zip

from dagster import Bool, Field, StringSource, check, resource, seven
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.events import log_step_event
from dagster.core.execution.plan.external_step import (
    PICKLED_EVENTS_FILE_NAME,
    PICKLED_STEP_RUN_REF_FILE_NAME,
    step_context_to_step_run_ref,
)
from dagster.serdes import deserialize_value

from .configs import define_databricks_storage_config, define_databricks_submit_run_config

CODE_ZIP_NAME = "code.zip"


@resource(
    {
        "run_config": define_databricks_submit_run_config(),
        "databricks_host": Field(
            StringSource,
            is_required=True,
            description="Databricks host, e.g. uksouth.azuredatabricks.com",
        ),
        "databricks_token": Field(
            StringSource, is_required=True, description="Databricks access token",
        ),
        "storage": define_databricks_storage_config(),
        "local_pipeline_package_path": Field(
            StringSource,
            is_required=True,
            description="Absolute path to the package that contains the pipeline definition(s) "
            "whose steps will execute remotely on Databricks. This is a path on the local "
            "fileystem of the process executing the pipeline. Before every step run, the "
            "launcher will zip up the code in this path, upload it to DBFS, and unzip it "
            "into the Python path of the remote Spark process. This gives the remote process "
            "access to up-to-date user code.",
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
            "several minutes to the job runtime.",
        ),
    }
)
def databricks_pyspark_step_launcher(context):
    """Resource for running solids as a Databricks Job.

    When this resource is used, the solid will be executed in Databricks using the 'Run Submit'
    API. Pipeline code will be zipped up and copied to a directory in DBFS along with the solid's
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
        databricks_host,
        databricks_token,
        storage,
        local_pipeline_package_path,
        staging_prefix,
        wait_for_logs,
    ):
        self.run_config = check.dict_param(run_config, "run_config")
        self.databricks_host = check.str_param(databricks_host, "databricks_host")
        self.databricks_token = check.str_param(databricks_token, "databricks_token")
        self.storage = check.dict_param(storage, "storage")
        self.local_pipeline_package_path = check.str_param(
            local_pipeline_package_path, "local_pipeline_package_path"
        )
        self.staging_prefix = check.str_param(staging_prefix, "staging_prefix")
        check.invariant(staging_prefix.startswith("/"), "staging_prefix must be an absolute path")
        self.wait_for_logs = check.bool_param(wait_for_logs, "wait_for_logs")

        self.databricks_runner = DatabricksJobRunner(host=databricks_host, token=databricks_token)

    def launch_step(self, step_context, prior_attempts_count):
        step_run_ref = step_context_to_step_run_ref(
            step_context, prior_attempts_count, self.local_pipeline_package_path
        )
        run_id = step_context.pipeline_run.run_id
        log = step_context.log

        step_key = step_run_ref.step_key
        self._upload_artifacts(log, step_run_ref, run_id, step_key)

        task = self._get_databricks_task(run_id, step_key)
        databricks_run_id = self.databricks_runner.submit_run(self.run_config, task)

        try:
            self.databricks_runner.wait_for_run_to_complete(log, databricks_run_id)
        finally:
            if self.wait_for_logs:
                self._log_logs_from_cluster(log, databricks_run_id)

        for event in self.get_step_events(run_id, step_key):
            log_step_event(step_context, event)
            yield event

    def get_step_events(self, run_id, step_key):
        path = self._dbfs_path(run_id, step_key, PICKLED_EVENTS_FILE_NAME)
        events_data = self.databricks_runner.client.read_file(path)
        return deserialize_value(pickle.loads(events_data))

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
            self._internal_dbfs_path(run_id, step_key, CODE_ZIP_NAME),
        ]
        return {"spark_python_task": {"python_file": python_file, "parameters": parameters}}

    def _upload_artifacts(self, log, step_run_ref, run_id, step_key):
        """Upload the step run ref and pyspark code to DBFS to run as a job."""

        log.info("Uploading main file to DBFS")
        main_local_path = self._main_file_local_path()
        with open(main_local_path, "rb") as infile:
            self.databricks_runner.client.put_file(
                infile, self._dbfs_path(run_id, step_key, self._main_file_name())
            )

        log.info("Uploading pipeline to DBFS")
        with seven.TemporaryDirectory() as temp_dir:
            # Zip and upload package containing pipeline
            zip_local_path = os.path.join(temp_dir, CODE_ZIP_NAME)
            build_pyspark_zip(zip_local_path, self.local_pipeline_package_path)
            with open(zip_local_path, "rb") as infile:
                self.databricks_runner.client.put_file(
                    infile, self._dbfs_path(run_id, step_key, CODE_ZIP_NAME)
                )

        log.info("Uploading step run ref file to DBFS")
        step_pickle_file = io.BytesIO()

        pickle.dump(step_run_ref, step_pickle_file)
        step_pickle_file.seek(0)
        self.databricks_runner.client.put_file(
            step_pickle_file, self._dbfs_path(run_id, step_key, PICKLED_STEP_RUN_REF_FILE_NAME),
        )

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

    def _dbfs_path(self, run_id, step_key, filename):
        path = "/".join([self.staging_prefix, run_id, step_key, os.path.basename(filename)])
        return "dbfs://{}".format(path)

    def _internal_dbfs_path(self, run_id, step_key, filename):
        """Scripts running on Databricks should access DBFS at /dbfs/."""
        path = "/".join([self.staging_prefix, run_id, step_key, os.path.basename(filename)])
        return "/dbfs/{}".format(path)
