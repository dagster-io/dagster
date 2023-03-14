"""Resource to run PySpark operations on EMR on EKS clusters."""
import dataclasses
import hashlib
import os
import time
from typing import Dict, Iterator
from urllib.parse import urlparse

import boto3
from dagster import (
    Array,
    Field,
    MetadataEntry,
    MetadataValue,
    Permissive,
    StringSource,
    check,
    resource,
)
from dagster._core.execution.plan.external_step import (
    PICKLED_STEP_RUN_REF_FILE_NAME,
)
from dagster.core.code_pointer import FileCodePointer, ModuleCodePointer
from dagster.core.definitions.step_launcher import StepRunRef
from dagster.core.errors import (
    DagsterExecutionInterruptedError,
    raise_execution_interrupts,
)
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    log_step_event,
)
from dagster.core.execution.context.system import StepExecutionContext
from dagster.core.execution.plan.external_step import step_context_to_step_run_ref
from dagster.core.execution.plan.objects import (
    ErrorSource,
    StepFailureData,
    UserFailureData,
)
from dagster_pyspark.resources import PySparkResource

from dagster_aws.emr.pyspark_step_launcher import (
    CODE_ZIP_NAME,
    EMR_PY_SPARK_STEP_LAUNCHER_BASE_CONFIG,
    EmrPySparkStepLauncherBase,
)

from . import emr_eks_step_main
from .monitor import EmrEksJobError, EmrEksJobRunMonitor

EMR_EKS_CONFIG_SCHEMA = dict(
    **EMR_PY_SPARK_STEP_LAUNCHER_BASE_CONFIG,
    **{
        "emr_release_label": Field(StringSource, description="EMR release label"),
        "container_image": Field(StringSource, description="Container image to use"),
        "job_role_arn": Field(StringSource, description="ARN of the role to use for job execution"),
        "log_group_name": Field(StringSource, description="Cloudwatch log group"),
        "additional_relative_paths": Field(
            Array(StringSource),
            description=(
                "List of relative relative paths which are not correctly reachable from the "
                "repository base. In practice let's say we have a package located at "
                "`/root/some/involved/path/target_package` it can still be imported "
                "as `target_package` if `some/involved/path/` is added to the list. "
                "This can be useful, for example, in case of git submodules."
            ),
            default_value=[],
        ),
        "log4j_conf": Field(Permissive(), default_value={}, is_required=False),
    },
)


@resource(config_schema=EMR_EKS_CONFIG_SCHEMA)
def emr_eks_pyspark_resource(context):
    spark_config = context.resource_config.get("spark_config")

    return EmrEksPySparkResource(
        cluster_id=context.resource_config.get("cluster_id"),
        container_image=context.resource_config.get("container_image"),
        deploy_local_job_package=context.resource_config.get("deploy_local_job_package"),
        emr_release_label=context.resource_config.get("emr_release_label"),
        job_role_arn=context.resource_config.get("job_role_arn"),
        log_group_name=context.resource_config.get("log_group_name"),
        log4j_conf=context.resource_config.get("log4j_conf"),
        region_name=context.resource_config.get("region_name"),
        staging_bucket=context.resource_config.get("staging_bucket"),
        staging_prefix=context.resource_config.get("staging_prefix"),
        spark_config=spark_config,
        ephemeral_instance=context.instance.is_ephemeral,
        additional_relative_paths=context.resource_config.get("additional_relative_paths"),
    )


class EmrEksPySparkResource(PySparkResource, EmrPySparkStepLauncherBase):
    """A PySpark resource where code is executed on a remote
    EMR on EKS cluster.

    Launching Steps on Remote Clusters
    ----------------------------------
    When this resource implementation is used as a ``PySparkResource``,
    a job run on EMR on EKS will be started, and the step will run there.
    This works by making the resource also inherit from ``StepLauncher``,
    and implement ``launch_step`` to serialize the definition of the step,
    run it on the remote cluster.

    Dagster operations produce events (e.g., when a step finishes, or when
    an output is produced). The events produced by the operation running
    on EMR on EKS in the Spark driver thus need to be serialized, sent
    back to the Dagster instance, and deserialized so that Dagster is
    aware of what happened in the remote cluster. Dagster events are not
    JSON serialized, and have to be pickled. As these events are small,
    the following procedure is used:

    - In the Spark driver, as part of the job entrypoint (``job_main.py``),
      events produced by the step are pickled, converted to Base64, and
      logged to ``stdout``.

    - Logs of the Spark driver are automatically reported by EMR to a
      CloudWatch log group.

    - The step launcher running on the original Dagster instance tails
      the CloudWatch logs. Logs are reported to Dagster. When an event
      is seen in a log record, it is decoded, unpickled, and sent to
      Dagster.

    Logs are uploaded to CloudWatch by EMR every 10s. As such, events may
    not be reported to Dagster in real time, and there can be some delay.
    Events will also often show up in Dagster in batches, when a batch
    of new logs has been pulled. Although more involved solution might
    allow to reduce latency (e.g., creating per-job run AWS SQS queues),
    using the logs should be good enough for now.

    Deploying Code
    --------------
    The resource supports two ways of deploying our Python code to the
    EMR on EKS jobs:

    - **Running a container that contains the code.** This is the target
      workflow for a cloud deployment.

      As part of a CI job, we create a docker image from the EMR base
      image, and add our Python virtual environment, as well as our Python
      code. To run a job, we directly run this docker image and do not need
      to upload anything else, as the code is baked in the image.

      New CI jobs update the docker image when the code is updated. With
      caching in docker builds, most of those builds will be fast as only
      the code changes, and the Python environment remains the same.

      This workflow is not amenable to local development, though.

    - **Running a container without the code, uploading the code at job
      submission**. This is the target workflow for local development.

      When submitting a job, a ZIP archive of the code is created and
      uploaded to S3. The Spark driver will then pull the ZIP archive,
      add it to the Python path, and use that to import modules.

      **Note**: Python implicit namespace packages are not supported.
      All packages **must** have an ``__init__.py`` to be importable
      in this workflow.

      **Note**: if the container used has some code, it will just be
      ignored. For instance, we can run with a container that has the code
      from `develop` or a previous version of the code from the branch. As
      we are staging the local code, code on the container will be ignored.

    The container-only workflow is selected automatically when the Dagster
    repository is seen to come from a docker image. In other cases, the
    code-upload workflow is used.
    """

    def __init__(
        self,
        cluster_id,
        container_image,
        deploy_local_job_package,
        emr_release_label,
        job_role_arn,
        log_group_name,
        log4j_conf,
        region_name,
        staging_bucket,
        staging_prefix,
        spark_config,
        ephemeral_instance,
        additional_relative_paths,
    ):
        EmrPySparkStepLauncherBase.__init__(
            self,
            region_name,
            staging_bucket,
            staging_prefix,
            deploy_local_job_package,
            cluster_id,
            spark_config,
            emr_eks_step_main.__file__,
        )

        self.container_image = check.str_param(container_image, "container_image")
        self.emr_release_label = check.str_param(emr_release_label, "emr_release_label")
        self.job_role_arn = check.str_param(job_role_arn, "job_role_arn")
        self.log_group_name = check.str_param(log_group_name, "log_group_name")
        self.additional_relative_paths = additional_relative_paths
        self.log4j_conf = log4j_conf

        # TODO: all this configuration business is extremely verbose. How can we
        # make it more streamlined? Each parameter is mentioned 4 times, and the
        # types are mentioned twices here and above.

        if ephemeral_instance:
            # The step launcher resource is first created in
            # the plan process, from where a job run is created.
            #
            # The resource is then created again when we run the
            # step in the Spark driver on the EMR cluster.
            #
            # A Spark session is only required in the latter case,
            # so we only create it on ephemeral Dagster instances
            # to avoid wasting time initializing a Spark session
            # that will not be used in the plan process.
            #
            # We do not pass any configuration to the session, as
            # it will be defined when we submit the job run instead.
            super(EmrEksPySparkResource, self).__init__({})

    def launch_step(self, step_context: StepExecutionContext) -> Iterator[DagsterEvent]:
        log = step_context.log
        application_name = self._application_name(step_context)

        # Determine type of submission and set container image
        if self.deploy_local_job_package:
            log.info("Local code will be staged")
        else:
            log.info(f"Using image '{self.container_image}' with code from repository origin")

        step_run_ref = self._step_run_ref(step_context)
        run_id = step_context.dagster_run.run_id
        step_key = step_context.step.key

        origin = step_run_ref.dagster_run.pipeline_code_origin

        self._post_artifacts(
            log,
            step_run_ref,
            run_id,
            step_key,
            origin.repository_origin.code_pointer.working_directory,
        )

        job_id = self._start_job_run(
            application_name,
            run_id,
            step_key,
        )

        yield from self.wait_for_completion_and_log(job_id, step_context)

    def wait_for_completion_and_log(
        self, job_id: str, step_context: StepExecutionContext
    ) -> Iterator[DagsterEvent]:
        def _log_event(event: DagsterEvent) -> Iterator[DagsterEvent]:
            """Log an event, and yield it. Both seem necessary."""
            log_step_event(step_context, event)
            yield event

        log = step_context.log

        yield from _log_event(self._startup_event(step_context, job_id))

        # Monitor Job Run
        monitor = EmrEksJobRunMonitor(cluster_id=self.cluster_id, region_name=self.region_name)

        ts_start_ms = int(time.time() * 1000) - 3600  # When to start polling logs

        with raise_execution_interrupts():
            try:
                for event in monitor.wait_for_completion(
                    log,
                    job_id,
                    self.log_group_name,
                    self._driver_log_stream_name(
                        job_id, self._sanitize_step_key(step_context.step.key)
                    ),
                    ts_start_ms,
                ):
                    if event.event_type_value == DagsterEventType.LOGS_CAPTURED:
                        # Do not report 'LOGS_CAPTURED' event from the remote
                        # execution: the local executor that is running the step
                        # launcher will already have emitted the event.
                        continue

                    # Report events produced in the Spark driver and
                    # logged in the driver's `stdout` back to Dagster.
                    yield from _log_event(event)

            except DagsterExecutionInterruptedError:
                # Job was interrupted, cancel the EMR on EKS Job Run.
                self._terminate_job_run(step_context)
                raise

            except EmrEksJobError as exc:
                # Job failed, report a proper `STEP_FAILURE` event with metadata.
                yield from _log_event(self._failure_event(step_context, exc))

    def _start_job_run(
        self,
        application_name: str,
        run_id: str,
        step_key: str,
    ) -> str:
        """Start EMR on EKS Job Run for the step."""
        driver_entrypoint = self._artifact_s3_uri(run_id, step_key, PICKLED_STEP_RUN_REF_FILE_NAME)

        # Configuration
        spark_config = dict(self.spark_config)

        # Determine type of submission and set container image

        spark_config["spark.kubernetes.container.image"] = self.container_image

        # Configure staging location
        upload_key = "spark.kubernetes.file.upload.path"

        if upload_key not in spark_config:
            spark_config[upload_key] = f"s3://{self.staging_bucket}/{self.staging_prefix}"

        spark_config["spark.kubernetes.driverEnv.ENV_PATHS"] = ",".join(
            self.additional_relative_paths
        )

        # Prepare and start the job
        configs = [
            {
                "classification": "spark-defaults",
                "properties": spark_config,
            },
            {"classification": "spark-log4j", "properties": self.log4j_conf},
        ]

        driver_kwargs = dict()

        if self.deploy_local_job_package:
            driver_kwargs[
                "sparkSubmitParameters"
            ] = f"--py-files {self._artifact_s3_uri(run_id, step_key, CODE_ZIP_NAME)}"

        response = self._emr_client().start_job_run(
            name=application_name,
            virtualClusterId=self.cluster_id,
            executionRoleArn=self.job_role_arn,
            releaseLabel=self.emr_release_label,
            jobDriver={
                "sparkSubmitJobDriver": {
                    "entryPoint": self._artifact_s3_uri(run_id, step_key, self._main_file_name()),
                    "entryPointArguments": [
                        self.staging_bucket,
                        urlparse(driver_entrypoint).path.lstrip("/"),
                    ],
                    **driver_kwargs,
                }
            },
            configurationOverrides={
                "applicationConfiguration": configs,
                "monitoringConfiguration": {
                    "cloudWatchMonitoringConfiguration": {
                        "logGroupName": self.log_group_name,
                        "logStreamNamePrefix": self._sanitize_step_key(step_key),
                    }
                },
            },
        )

        return response["id"]

    def _terminate_job_run(self, step_context: StepExecutionContext) -> None:
        """Cancel the job run for a step."""
        log = step_context.log
        application_name = self._application_name(step_context)

        emr_client = self._emr_client()

        resp = emr_client.list_job_runs(virtualClusterId=self.cluster_id, name=application_name)
        job_runs = resp["jobRuns"]

        assert len(job_runs) == 1, "Exactly one job run should match"

        log.info(f"Cancelling job run for application '{application_name}'")
        emr_client.cancel_job_run(virtualClusterId=self.cluster_id, id=job_runs[0]["id"])

    def _application_name(self, step_context: StepExecutionContext) -> str:
        """Spark application name for the step run."""
        run_name = step_context.dagster_run.pipeline_name
        run_id = step_context.dagster_run.run_id
        step_key = step_context.step.key

        name = f"{run_name}-{step_key}-{run_id}"
        name_hashed = hashlib.sha256(name.encode("utf-8")).hexdigest()

        # EMR on EKS job run names are limited to 64 chars. See
        # <https://docs.aws.amazon.com/emr-on-eks/latest/APIReference/API_StartJobRun.html>.
        # Use 32 chars for the clear text name, and 32 chars for the unique identifier.
        return name[:32] + name_hashed[:32]

    def _job_log_streams_prefix(self, job_id: str, log_prefix: str) -> str:
        """Common prefix for CloudWatch Logs streams of the job."""
        return f"{log_prefix}/{self.cluster_id}/jobs/{job_id}/"

    def _driver_log_stream_name(self, job_id: str, log_prefix: str) -> str:
        """CloudWatch Logs stream name for the Spark driver."""
        return (
            self._job_log_streams_prefix(job_id, log_prefix)
            + f"containers/spark-{job_id}/spark-{job_id}-driver/"
        )

    def _job_log_streams_url(self, job_id: str, log_prefix: str) -> str:
        """CloudWatch Logs URL."""
        log_stream_name = self._job_log_streams_prefix(job_id, log_prefix).replace("/", "$252F")

        return (
            f"https://{self.region_name}.console.aws.amazon.com/cloudwatch/home?"
            f"region={self.region_name}#logsV2:"
            f"log-groups/log-group/{self.log_group_name}$3F"
            f"logStreamNameFilter$3D{log_stream_name}"
        )

    def _cluster_url(self) -> str:
        return (
            f"https://{self.region_name}.console.aws.amazon.com/elasticmapreduce/home?"
            f"region={self.region_name}#virtual-cluster-jobs:{self.cluster_id}"
        )

    def _check_spark_conf(self):
        required_keys = {"spark.pyspark.python", "spark.pyspark.driver.python"}

        for key in required_keys:
            assert key in self.spark_conf, f"Key {key} must be provided in the Spark configuration"

    def _job_event_metadata(self, job_id: str, log_prefix: str) -> Dict[str, MetadataValue]:
        return {
            "EMR on EKS Cluster": MetadataValue.url(self._cluster_url()),
            "\u1217 Job log streams": MetadataValue.url(
                self._job_log_streams_url(job_id, log_prefix),
            ),
            "Job ID": MetadataValue.text(job_id),
        }

    def _startup_event(self, step_context: StepExecutionContext, job_id: str) -> DagsterEvent:
        return DagsterEvent(
            event_type_value=DagsterEventType.ENGINE_EVENT.value,
            pipeline_name=step_context.dagster_run.pipeline_name,
            step_key=step_context.step.key,
            message="Created Job Run",
            event_specific_data=EngineEventData(
                metadata_entries=[
                    MetadataEntry(label=k, value=v)
                    for k, v in self._job_event_metadata(
                        job_id, self._sanitize_step_key(step_context.step.key)
                    ).items()
                ]
            ),
        )

    def _failure_event(
        self, step_context: StepExecutionContext, exc: EmrEksJobError
    ) -> DagsterEvent:
        """Build a Dagster step failure event from a job exception."""
        application_name = self._application_name(step_context)

        return DagsterEvent(
            event_type_value=DagsterEventType.STEP_FAILURE.value,
            pipeline_name=step_context.dagster_run.pipeline_name,
            step_key=step_context.step.key,
            message=f"Spark job for '{application_name}' has failed",
            event_specific_data=StepFailureData(
                error=None,
                user_failure_data=UserFailureData(
                    label="Spark job error",
                    metadata_entries=[
                        MetadataEntry(label=k, value=MetadataValue.text(v))
                        for k, v in dataclasses.asdict(exc).items()
                    ],
                ),
                error_source=ErrorSource.USER_CODE_ERROR,
            ),
        )

    def _step_run_ref(
        self,
        step_context: StepExecutionContext,
    ) -> StepRunRef:
        """Build a StepRunRef that can be used to run the step
        in a remote process.
        """
        step_run_ref = step_context_to_step_run_ref(
            step_context,
        )

        if not self.deploy_local_job_package:
            # Container has the code, but we need to point Dagster to it
            step_run_ref = EmrEksPySparkResource._set_step_run_ref_working_directory(step_run_ref)

        step_run_ref = EmrEksPySparkResource._remove_parent_run_id(step_run_ref)

        return step_run_ref

    @staticmethod
    def _set_step_run_ref_working_directory(
        step_run_ref: StepRunRef,
        working_directory: str = "/opt/raptor/pipelines/",  # TODO: do not hardcode
    ) -> StepRunRef:
        """Hack for submitting code at a different location in the remote
        containers as locally.
        """
        if isinstance(step_run_ref.recon_pipeline.repository.pointer, FileCodePointer):
            step_run_ref = step_run_ref._replace(
                recon_pipeline=step_run_ref.recon_pipeline._replace(
                    repository=step_run_ref.recon_pipeline.repository._replace(
                        pointer=ModuleCodePointer(
                            step_run_ref.recon_pipeline.repository.pointer.module,
                            step_run_ref.recon_pipeline.repository.pointer.fn_name,
                            working_directory,
                        )
                    )
                )
            )

        return step_run_ref

    @staticmethod
    def _remove_parent_run_id(step_run_ref: StepRunRef) -> StepRunRef:
        """Hack to remove parent run ID for the remote step run ref.

        As an ephemeral Dagster instance is used, the parent run IDs cause
        issues as they are not known to the ephemeral instance.
        """
        return step_run_ref._replace(
            dagster_run=step_run_ref.dagster_run._replace(root_run_id=None)._replace(
                parent_run_id=None
            )
        )

    def _emr_client(self):
        return boto3.client("emr-containers", region_name=self.region_name)

    def _s3_client(self):
        return boto3.client("s3", region_name=self.region_name)

    def _main_file_name(self):
        return os.path.basename(self._main_file_local_path())

    def _main_file_local_path(self):
        return emr_eks_step_main.__file__

    def _sanitize_step_key(self, step_key: str) -> str:
        # step_keys of dynamic steps contain brackets, which are invalid characters
        return step_key.replace("[", "__").replace("]", "__")

    def _artifact_s3_uri(self, run_id, step_key, filename):
        key = self._artifact_s3_key(run_id, self._sanitize_step_key(step_key), filename)
        return "s3://{bucket}/{key}".format(bucket=self.staging_bucket, key=key)

    def _artifact_s3_key(self, run_id, step_key, filename):
        return "/".join(
            [
                self.staging_prefix,
                run_id,
                self._sanitize_step_key(step_key),
                os.path.basename(filename),
            ]
        )
