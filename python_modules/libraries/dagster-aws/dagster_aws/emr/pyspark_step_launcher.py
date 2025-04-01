import os
import pickle
import sys
import tempfile
import time

import boto3
from botocore.exceptions import ClientError
from dagster import (
    Field,
    StringSource,
    _check as check,
    resource,
)
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.definitions.step_launcher import StepLauncher, _step_launcher_supersession
from dagster._core.errors import DagsterInvariantViolationError, raise_execution_interrupts
from dagster._core.execution.plan.external_step import (
    PICKLED_EVENTS_FILE_NAME,
    PICKLED_STEP_RUN_REF_FILE_NAME,
    step_context_to_step_run_ref,
)
from dagster._serdes import deserialize_value

from dagster_aws.emr import EmrError, EmrJobRunner, emr_step_main
from dagster_aws.emr.configs_spark import spark_config as get_spark_config
from dagster_aws.utils.mrjob.log4j import parse_hadoop_log4j_records

# On EMR, Spark is installed here
EMR_SPARK_HOME = "/usr/lib/spark/"

CODE_ZIP_NAME = "code.zip"


@dagster_maintained_resource
@resource(
    {
        "spark_config": get_spark_config(),
        "cluster_id": Field(
            StringSource, description="Name of the job flow (cluster) on which to execute."
        ),
        "region_name": Field(StringSource, description="The AWS region that the cluster is in."),
        "action_on_failure": Field(
            str,
            is_required=False,
            default_value="CANCEL_AND_WAIT",
            description=(
                "The EMR action to take when the cluster step fails: "
                "https://docs.aws.amazon.com/emr/latest/APIReference/API_StepConfig.html"
            ),
        ),
        "staging_bucket": Field(
            StringSource,
            is_required=True,
            description=(
                "S3 bucket to use for passing files between the plan process and EMR process."
            ),
        ),
        "staging_prefix": Field(
            StringSource,
            is_required=False,
            default_value="emr_staging",
            description=(
                "S3 key prefix inside the staging_bucket to use for files passed the plan "
                "process and EMR process"
            ),
        ),
        "wait_for_logs": Field(
            bool,
            is_required=False,
            default_value=False,
            description=(
                "If set, the system will wait for EMR logs to appear on S3. Note that logs "
                "are copied every 5 minutes, so enabling this will add several minutes to the job "
                "runtime."
            ),
        ),
        "local_job_package_path": Field(
            StringSource,
            is_required=False,
            description=(
                "Absolute path to the package that contains the job definition(s) whose steps will"
                " execute remotely on EMR. This is a path on the local fileystem of the process"
                " executing the job. The expectation is that this package will also be available on"
                " the python path of the launched process running the Spark step on EMR, either"
                " deployed on step launch via the deploy_local_job_package option, referenced on s3"
                " via the s3_job_package_path option, or installed on the cluster via bootstrap"
                " actions."
            ),
        ),
        "local_pipeline_package_path": Field(
            StringSource,
            is_required=False,
            description=(
                "(legacy) Absolute path to the package that contains the pipeline definition(s)"
                " whose steps will execute remotely on EMR. This is a path on the local fileystem"
                " of the process executing the pipeline. The expectation is that this package will"
                " also be available on the python path of the launched process running the Spark"
                " step on EMR, either deployed on step launch via the deploy_local_pipeline_package"
                " option, referenced on s3 via the s3_pipeline_package_path option, or installed on"
                " the cluster via bootstrap actions."
            ),
        ),
        "deploy_local_job_package": Field(
            bool,
            default_value=False,
            is_required=False,
            description=(
                "If set, before every step run, the launcher will zip up all the code in"
                " local_job_package_path, upload it to s3, and pass it to spark-submit's --py-files"
                " option. This gives the remote process access to up-to-date user code. If not set,"
                " the assumption is that some other mechanism is used for distributing code to the"
                " EMR cluster. If this option is set to True, s3_job_package_path should not also"
                " be set."
            ),
        ),
        "deploy_local_pipeline_package": Field(
            bool,
            default_value=False,
            is_required=False,
            description=(
                "(legacy) If set, before every step run, the launcher will zip up all the code in"
                " local_job_package_path, upload it to s3, and pass it to spark-submit's --py-files"
                " option. This gives the remote process access to up-to-date user code. If not set,"
                " the assumption is that some other mechanism is used for distributing code to the"
                " EMR cluster. If this option is set to True, s3_job_package_path should not also"
                " be set."
            ),
        ),
        "s3_job_package_path": Field(
            StringSource,
            is_required=False,
            description=(
                "If set, this path will be passed to the --py-files option of spark-submit. "
                "This should usually be a path to a zip file.  If this option is set, "
                "deploy_local_job_package should not be set to True."
            ),
        ),
        "s3_pipeline_package_path": Field(
            StringSource,
            is_required=False,
            description=(
                "If set, this path will be passed to the --py-files option of spark-submit. "
                "This should usually be a path to a zip file.  If this option is set, "
                "deploy_local_pipeline_package should not be set to True."
            ),
        ),
    }
)
@_step_launcher_supersession
def emr_pyspark_step_launcher(context):
    # Resolve legacy arguments
    if context.resource_config.get("local_job_package_path") and context.resource_config.get(
        "local_pipeline_package_path"
    ):
        raise DagsterInvariantViolationError(
            "Provided both ``local_job_package_path`` and legacy version "
            "``local_pipeline_package_path`` arguments to ``emr_pyspark_step_launcher`` "
            "resource. Please choose one or the other."
        )

    if not context.resource_config.get(
        "local_job_package_path"
    ) and not context.resource_config.get("local_pipeline_package_path"):
        raise DagsterInvariantViolationError(
            "For resource ``emr_pyspark_step_launcher``, no config value provided for required "
            "schema entry ``local_job_package_path``."
        )

    local_job_package_path = context.resource_config.get(
        "local_job_package_path"
    ) or context.resource_config.get("local_pipeline_package_path")

    if context.resource_config.get("deploy_local_job_package") and context.resource_config.get(
        "deploy_local_pipeline_package"
    ):
        raise DagsterInvariantViolationError(
            "Provided both ``deploy_local_job_package`` and legacy version "
            "``deploy_local_pipeline_package`` arguments to ``emr_pyspark_step_launcher`` "
            "resource. Please choose one or the other."
        )

    deploy_local_job_package = context.resource_config.get(
        "deploy_local_job_package"
    ) or context.resource_config.get("deploy_local_pipeline_package")

    if context.resource_config.get("s3_job_package_path") and context.resource_config.get(
        "s3_pipeline_package_path"
    ):
        raise DagsterInvariantViolationError(
            "Provided both ``s3_job_package_path`` and legacy version "
            "``s3_pipeline_package_path`` arguments to ``emr_pyspark_step_launcher`` "
            "resource. Please choose one or the other."
        )

    s3_job_package_path = context.resource_config.get(
        "s3_job_package_path"
    ) or context.resource_config.get("s3_pipeline_package_path")

    return EmrPySparkStepLauncher(
        region_name=context.resource_config.get("region_name"),
        staging_bucket=context.resource_config.get("staging_bucket"),
        staging_prefix=context.resource_config.get("staging_prefix"),
        wait_for_logs=context.resource_config.get("wait_for_logs"),
        action_on_failure=context.resource_config.get("action_on_failure"),
        cluster_id=context.resource_config.get("cluster_id"),
        spark_config=context.resource_config.get("spark_config"),
        local_job_package_path=local_job_package_path,
        deploy_local_job_package=deploy_local_job_package,
        s3_job_package_path=s3_job_package_path,
    )


emr_pyspark_step_launcher.__doc__ = "\n".join(
    "- **" + option + "**: " + (field.description or "")
    for option, field in emr_pyspark_step_launcher.config_schema.config_type.fields.items()  # type: ignore
)


@_step_launcher_supersession
class EmrPySparkStepLauncher(StepLauncher):
    def __init__(
        self,
        region_name,
        staging_bucket,
        staging_prefix,
        wait_for_logs,
        action_on_failure,
        cluster_id,
        spark_config,
        local_job_package_path,
        deploy_local_job_package,
        s3_job_package_path=None,
    ):
        self.region_name = check.str_param(region_name, "region_name")
        self.staging_bucket = check.str_param(staging_bucket, "staging_bucket")
        self.staging_prefix = check.str_param(staging_prefix, "staging_prefix")
        self.wait_for_logs = check.bool_param(wait_for_logs, "wait_for_logs")
        self.action_on_failure = check.str_param(action_on_failure, "action_on_failure")
        self.cluster_id = check.str_param(cluster_id, "cluster_id")
        self.spark_config = spark_config

        check.invariant(
            not deploy_local_job_package or not s3_job_package_path,
            "If deploy_local_job_package is set to True, s3_job_package_path should not "
            "also be set.",
        )

        self.local_job_package_path = check.str_param(
            local_job_package_path, "local_job_package_path"
        )
        self.deploy_local_job_package = check.bool_param(
            deploy_local_job_package, "deploy_local_job_package"
        )
        self.s3_job_package_path = check.opt_str_param(s3_job_package_path, "s3_job_package_path")

        self.emr_job_runner = EmrJobRunner(region=self.region_name)

    def _post_artifacts(self, log, step_run_ref, run_id, step_key):
        """Synchronize the step run ref and pyspark code to an S3 staging bucket for use on EMR.

        For the zip file, consider the following toy example:

            # Folder: my_pyspark_project/
            # a.py
            def foo():
                print(1)

            # b.py
            def bar():
                print(2)

            # main.py
            from a import foo
            from b import bar

            foo()
            bar()

        This will zip up `my_pyspark_project/` as `my_pyspark_project.zip`. Then, when running
        `spark-submit --py-files my_pyspark_project.zip emr_step_main.py` on EMR this will
        print 1, 2.
        """
        from dagster_pyspark.utils import build_pyspark_zip

        with tempfile.TemporaryDirectory() as temp_dir:
            s3 = boto3.client("s3", region_name=self.region_name)

            # Upload step run ref
            def _upload_file_to_s3(local_path, s3_filename):
                key = self._artifact_s3_key(run_id, step_key, s3_filename)
                s3_uri = self._artifact_s3_uri(run_id, step_key, s3_filename)
                log.debug(f"Uploading file {local_path} to {s3_uri}")
                s3.upload_file(Filename=local_path, Bucket=self.staging_bucket, Key=key)

            # Upload main file.
            # The remote Dagster installation should also have the file, but locating it there
            # could be a pain.
            main_local_path = self._main_file_local_path()
            _upload_file_to_s3(main_local_path, self._main_file_name())

            if self.deploy_local_job_package:
                # Zip and upload package containing job
                zip_local_path = os.path.join(temp_dir, CODE_ZIP_NAME)

                build_pyspark_zip(zip_local_path, self.local_job_package_path)
                _upload_file_to_s3(zip_local_path, CODE_ZIP_NAME)

            # Create step run ref pickle file
            step_run_ref_local_path = os.path.join(temp_dir, PICKLED_STEP_RUN_REF_FILE_NAME)
            with open(step_run_ref_local_path, "wb") as step_pickle_file:
                pickle.dump(step_run_ref, step_pickle_file)

            _upload_file_to_s3(step_run_ref_local_path, PICKLED_STEP_RUN_REF_FILE_NAME)

    def launch_step(self, step_context):
        step_run_ref = step_context_to_step_run_ref(step_context, self.local_job_package_path)

        run_id = step_context.dagster_run.run_id
        log = step_context.log

        step_key = step_run_ref.step_key
        self._post_artifacts(log, step_run_ref, run_id, step_key)

        emr_step_def = self._get_emr_step_def(run_id, step_key, step_context.op.name)
        emr_step_id = self.emr_job_runner.add_job_flow_steps(log, self.cluster_id, [emr_step_def])[
            0
        ]

        yield from self.wait_for_completion_and_log(run_id, step_key, emr_step_id, step_context)

    def wait_for_completion_and_log(self, run_id, step_key, emr_step_id, step_context):
        s3 = boto3.resource("s3", region_name=self.region_name)
        try:
            yield from self.wait_for_completion(step_context, s3, run_id, step_key, emr_step_id)
        except EmrError as emr_error:
            if self.wait_for_logs:
                self._log_logs_from_s3(step_context.log, emr_step_id)
            raise emr_error

        if self.wait_for_logs:
            self._log_logs_from_s3(step_context.log, emr_step_id)

    def wait_for_completion(
        self, step_context, s3, run_id, step_key, emr_step_id, check_interval=15
    ):
        """We want to wait for the EMR steps to complete, and while that's happening, we want to
        yield any events that have been written to S3 for us by the remote process.
        After the EMR steps complete, we want a final chance to fetch events before finishing
        the step.
        """
        done = False
        all_events = []
        # If this is being called within a `capture_interrupts` context, allow interrupts
        # while waiting for the pyspark execution to complete, so that we can terminate slow or
        # hanging steps
        while not done:
            with raise_execution_interrupts():
                time.sleep(check_interval)  # AWS rate-limits us if we poll it too often
                done = self.emr_job_runner.is_emr_step_complete(
                    step_context.log, self.cluster_id, emr_step_id
                )

                all_events_new = self.read_events(s3, run_id, step_key)

            if len(all_events_new) > len(all_events):  # pyright: ignore[reportArgumentType]
                for i in range(len(all_events), len(all_events_new)):  # pyright: ignore[reportArgumentType]
                    event = all_events_new[i]  # pyright: ignore[reportOptionalSubscript,reportArgumentType,reportIndexIssue]
                    # write each event from the EMR instance to the local instance
                    step_context.instance.handle_new_event(event)
                    if event.is_dagster_event:  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                        yield event.dagster_event  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                all_events = all_events_new

    def read_events(self, s3, run_id, step_key):
        events_s3_obj = s3.Object(
            self.staging_bucket, self._artifact_s3_key(run_id, step_key, PICKLED_EVENTS_FILE_NAME)
        )

        try:
            events_data = events_s3_obj.get()["Body"].read()
            return deserialize_value(pickle.loads(events_data))
        except ClientError as ex:
            # The file might not be there yet, which is fine
            if ex.response["Error"]["Code"] == "NoSuchKey":  # pyright: ignore[reportTypedDictNotRequiredAccess]
                return []
            else:
                raise ex

    def _log_logs_from_s3(self, log, emr_step_id):
        """Retrieves the logs from the remote PySpark process that EMR posted to S3 and logs
        them to the given log.
        """
        stdout_log, stderr_log = self.emr_job_runner.retrieve_logs_for_step_id(
            log, self.cluster_id, emr_step_id
        )
        # Since stderr is YARN / Hadoop Log4J output, parse and reformat those log lines for
        # Dagster's logging system.
        records = parse_hadoop_log4j_records(stderr_log)
        for record in records:
            if record.level:
                log.log(
                    level=record.level,
                    msg="".join(["Spark Driver stderr: ", record.logger, ": ", record.message]),
                )
            else:
                log.debug(f"Spark Driver stderr: {record.message}")

        sys.stdout.write(
            "---------- Spark Driver stdout: ----------\n"
            + stdout_log
            + "\n"
            + "---------- End of Spark Driver stdout ----------\n"
        )

    def _get_emr_step_def(self, run_id, step_key, solid_name):
        """From the local Dagster instance, construct EMR steps that will kick off execution on a
        remote EMR cluster.
        """
        from dagster_spark.utils import flatten_dict, format_for_cli

        action_on_failure = self.action_on_failure

        # Execute Solid via spark-submit
        conf = dict(flatten_dict(self.spark_config))
        conf["spark.app.name"] = conf.get("spark.app.name", solid_name)

        check.invariant(
            conf.get("spark.master", "yarn") == "yarn",
            desc=(
                "spark.master is configured as {}; cannot set Spark master on EMR to anything "
                'other than "yarn"'
            ).format(conf.get("spark.master")),
        )

        command = (
            [
                EMR_SPARK_HOME + "bin/spark-submit",
                "--master",
                "yarn",
                "--deploy-mode",
                conf.get("spark.submit.deployMode", "client"),
            ]
            + format_for_cli(list(flatten_dict(conf)))
            + [
                "--py-files",
                self._artifact_s3_uri(run_id, step_key, CODE_ZIP_NAME),
                self._artifact_s3_uri(run_id, step_key, self._main_file_name()),
                self.staging_bucket,
                self._artifact_s3_key(run_id, step_key, PICKLED_STEP_RUN_REF_FILE_NAME),
            ]
        )

        return EmrJobRunner.construct_step_dict_for_command(
            f"Execute Solid/Op {solid_name}", command, action_on_failure=action_on_failure
        )

    def _main_file_name(self):
        return os.path.basename(self._main_file_local_path())

    def _main_file_local_path(self):
        return emr_step_main.__file__

    def _sanitize_step_key(self, step_key: str) -> str:
        # step_keys of dynamic steps contain brackets, which are invalid characters
        return step_key.replace("[", "__").replace("]", "__")

    def _artifact_s3_uri(self, run_id, step_key, filename):
        key = self._artifact_s3_key(run_id, self._sanitize_step_key(step_key), filename)
        return f"s3://{self.staging_bucket}/{key}"

    def _artifact_s3_key(self, run_id, step_key, filename):
        return "/".join(
            [
                self.staging_prefix,
                run_id,
                self._sanitize_step_key(step_key),
                os.path.basename(filename),
            ]
        )
