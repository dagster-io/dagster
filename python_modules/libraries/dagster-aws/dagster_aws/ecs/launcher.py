import json
import warnings
from collections import namedtuple
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from dagster import Array, Enum, EnumValue, Field, Noneable, Permissive, ScalarUnion, StringSource
from dagster import _check as check
from dagster._core.events import EngineEventData, MetadataEntry
from dagster._core.launcher.base import (
    CheckRunHealthResult,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._core.storage.pipeline_run import PipelineRun
from dagster._grpc.types import ExecuteRunArgs
from dagster._serdes import ConfigurableClass

from ..secretsmanager import get_secrets_from_arns
from .container_context import SHARED_ECS_SCHEMA, EcsContainerContext
from .tasks import (
    DagsterEcsTaskConfig,
    DagsterEcsTaskDefinitionConfig,
    get_current_ecs_task,
    get_current_ecs_task_metadata,
    get_task_config_from_current_task,
    get_task_definition_dict_from_current_task,
)
from .utils import sanitize_family, should_assign_public_ip

Tags = namedtuple("Tags", ["arn", "cluster", "cpu", "memory"])

RUNNING_STATUSES = [
    "PROVISIONING",
    "PENDING",
    "ACTIVATING",
    "RUNNING",
    "DEACTIVATING",
    "STOPPING",
    "DEPROVISIONING",
]
STOPPED_STATUSES = ["STOPPED"]


class EcsRunLauncher(RunLauncher, ConfigurableClass):
    """RunLauncher that starts a task in ECS for each Dagster job run."""

    def __init__(
        self,
        inst_data=None,
        task_definition=None,
        container_name="run",
        secrets=None,
        secrets_tag="dagster",
        env_vars=None,
        include_sidecars=False,
        use_current_ecs_task=True,
        cluster: Optional[str] = None,
        subnets: Optional[List[str]] = None,
        security_group_ids: Optional[List[str]] = None,
        execution_role_arn: Optional[str] = None,
        task_role_arn: Optional[str] = None,
        log_group: Optional[str] = None,
        sidecar_container_definitions: Optional[List[Dict[str, Any]]] = None,
        launch_type: Optional[str] = None,
    ):
        self._inst_data = inst_data
        self.ecs = boto3.client("ecs")
        self.ec2 = boto3.resource("ec2")
        self.secrets_manager = boto3.client("secretsmanager")
        self.logs = boto3.client("logs")

        self.task_definition = task_definition
        self.container_name = container_name

        self.secrets = check.opt_list_param(secrets, "secrets")

        self.env_vars = check.opt_list_param(env_vars, "env_vars")

        if self.secrets and all(isinstance(secret, str) for secret in self.secrets):
            warnings.warn(
                "Setting secrets as a list of ARNs is deprecated. "
                "Secrets should instead follow the same structure as the ECS API: "
                "https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html",
                DeprecationWarning,
            )
            self.secrets = [
                {"name": name, "valueFrom": value_from}
                for name, value_from in get_secrets_from_arns(
                    self.secrets_manager, self.secrets
                ).items()
            ]

        self.secrets_tags = [secrets_tag] if secrets_tag else []
        self.include_sidecars = include_sidecars

        self.use_current_ecs_task = check.bool_param(use_current_ecs_task, "use_current_ecs_task")

        if self.task_definition:
            task_definition = self.ecs.describe_task_definition(taskDefinition=task_definition)
            container_names = [
                container.get("name")
                for container in task_definition["taskDefinition"]["containerDefinitions"]
            ]
            check.invariant(
                container_name in container_names,
                f"Cannot override container '{container_name}' in task definition "
                f"'{self.task_definition}' because the container is not defined.",
            )
            self.task_definition = task_definition["taskDefinition"]["taskDefinitionArn"]

        self.cluster = check.opt_str_param(cluster, "cluster")
        self.subnets = check.opt_list_param(subnets, "subnets")
        self.security_group_ids = check.opt_list_param(security_group_ids, "security_group_ids")
        self.execution_role_arn = check.opt_str_param(execution_role_arn, "execution_role_arn")
        self.task_role_arn = check.opt_str_param(task_role_arn, "task_role_arn")
        self.log_group = check.opt_str_param(log_group, "log_group")
        self.sidecar_container_definitions = check.opt_list_param(
            sidecar_container_definitions, "sidecar_container_definitions"
        )
        self.launch_type = check.opt_str_param(launch_type, "launch_type", default="FARGATE")

        if not self.use_current_ecs_task:
            check.invariant(
                self.cluster,
                "Must set a cluster if not pulling from current task definition",
            )
            check.invariant(
                self.subnets,
                "Must set subnets if not pulling from current task definition",
            )
            check.invariant(
                self.execution_role_arn,
                "Must set execution_role_arn if not pulling from current task definition",
            )
            check.invariant(
                not self.include_sidecars,
                "can only set include_sidecars if use_current_ecs_task is True",
            )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "task_definition": Field(
                StringSource,
                is_required=False,
                description=(
                    "The task definition to use when launching new tasks. "
                    "If none is provided, each run will create its own task "
                    "definition."
                ),
            ),
            "container_name": Field(
                StringSource,
                is_required=False,
                default_value="run",
                description=(
                    "The container name to use when launching new tasks. Defaults to 'run'."
                ),
            ),
            "secrets": Field(
                Array(
                    ScalarUnion(
                        scalar_type=str,
                        non_scalar_schema={"name": StringSource, "valueFrom": StringSource},
                    )
                ),
                is_required=False,
                description=(
                    "An array of AWS Secrets Manager secrets. These secrets will "
                    "be mounted as environment variables in the container. See "
                    "https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html."
                ),
            ),
            "secrets_tag": Field(
                Noneable(StringSource),
                is_required=False,
                default_value="dagster",
                description=(
                    "AWS Secrets Manager secrets with this tag will be mounted as "
                    "environment variables in the container. Defaults to 'dagster'."
                ),
            ),
            "include_sidecars": Field(
                bool,
                is_required=False,
                default_value=False,
                description=(
                    "Whether each run should use the same sidecars as the task that launches it. "
                    "Defaults to False."
                ),
            ),
            "use_current_ecs_task": Field(
                bool,
                is_required=False,
                default_value=True,
                description=(
                    "Whether to use the current task to configure the task definition and task "
                    "for the launched run - allows you to launch a run without specifying the "
                    "cluster/subnets/roles/etc. Requires that the launcher is running within an ECS "
                    "cluster. Individual fields like cluster or subnets can still be overriden "
                    "while this field is true."
                ),
            ),
            "cluster": Field(
                StringSource,
                is_required=False,
                description="Name of the ECS cluster to launch ECS tasks in.",
            ),
            "subnets": Field(
                Array(StringSource),
                is_required=False,
                description="List of subnets to use for the launched ECS task.",
            ),
            "security_group_ids": Field(
                Array(StringSource),
                is_required=False,
                description="Security group IDs to use for the launched ECS tasks.",
            ),
            "execution_role_arn": Field(
                StringSource,
                is_required=False,
                description=(
                    "IAM role that grants permissions to start the containers "
                    "defined in the launched ECS task."
                ),
            ),
            "task_role_arn": Field(
                StringSource,
                is_required=False,
                description="IAM role for the code within the launched ECS task.",
            ),
            "log_group": Field(
                StringSource,
                is_required=False,
                description="AWS log group for the launched ECS task.",
            ),
            "sidecar_container_definitions": Field(
                Array(Permissive({})),
                is_required=False,
                description=(
                    "List of container definitions to be included in the launched task in addition "
                    "to the main Dagster container. See the containerDefinitions argument to "
                    "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.register_task_definition"
                    " for the expected format."
                ),
            ),
            "launch_type": Field(
                Enum(
                    "EcsLaunchType",
                    [
                        EnumValue("FARGATE"),
                        EnumValue("EC2"),
                    ],
                ),
                is_required=False,
                default_value="FARGATE",
                description=(
                    "What type of ECS infrastructure to launch the run task in. "
                    "See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_types.html"
                ),
            ),
            **SHARED_ECS_SCHEMA,
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EcsRunLauncher(inst_data=inst_data, **config_value)

    def _set_ecs_tags(self, run_id, task_arn):
        try:
            tags = [{"key": "dagster/run_id", "value": run_id}]
            self.ecs.tag_resource(resourceArn=task_arn, tags=tags)
        except ClientError:
            pass

    def _set_run_tags(self, run_id: str, cluster: str, task_arn: str):
        tags = {
            "ecs/task_arn": task_arn,
            "ecs/cluster": cluster,
        }
        self._instance.add_run_tags(run_id, tags)

    def _get_run_tags(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        tags = run.tags if run else {}
        arn = tags.get("ecs/task_arn")
        cluster = tags.get("ecs/cluster")
        cpu = tags.get("ecs/cpu")
        memory = tags.get("ecs/memory")

        return Tags(arn, cluster, cpu, memory)

    def launch_run(self, context: LaunchRunContext) -> None:

        """
        Launch a run in an ECS task.

        Currently, Fargate is the only supported launchType and awsvpc is the
        only supported networkMode. These are the defaults that are set up by
        docker-compose when you use the Dagster ECS reference deployment.
        """
        run = context.pipeline_run
        container_context = EcsContainerContext.create_for_run(run, self)

        pipeline_origin = check.not_none(context.pipeline_code_origin)
        image = pipeline_origin.repository_origin.container_image

        # ECS limits overrides to 8192 characters including json formatting
        # https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RunTask.html
        # When container_context is serialized as part of the ExecuteRunArgs, we risk
        # going over this limit (for example, if many secrets have been set). This strips
        # the container context off of our pipeline origin because we don't actually need
        # it to launch the run; we only needed it to create the task definition.
        repository_origin = pipeline_origin.repository_origin
        # pylint: disable=protected-access
        stripped_repository_origin = repository_origin._replace(container_context={})
        stripped_pipeline_origin = pipeline_origin._replace(
            repository_origin=stripped_repository_origin
        )
        # pylint: enable=protected-access

        args = ExecuteRunArgs(
            pipeline_origin=stripped_pipeline_origin,
            pipeline_run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
        )
        command = args.get_command_args()

        task_config = self._task_config(run, image, container_context)

        # Set cpu or memory overrides
        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
        cpu_and_memory_overrides = self.get_cpu_and_memory_overrides(run)

        task_overrides = self._get_task_overrides(run)

        container_overrides = [
            {
                "name": self.container_name,
                "command": command,
                # containerOverrides expects cpu/memory as integers
                **{k: int(v) for k, v in cpu_and_memory_overrides.items()},
            }
        ]

        overrides: Dict[str, Any] = {
            "containerOverrides": container_overrides,
            # taskOverrides expects cpu/memory as strings
            **cpu_and_memory_overrides,
            **task_overrides,
        }

        # Run a task using the same network configuration as this processes's
        # task.

        run_task_params = dict(
            taskDefinition=task_config.task_definition,
            cluster=task_config.cluster,
            overrides=overrides,
            launchType=task_config.launch_type,
        )

        network_configuration = task_config.network_configuration
        if network_configuration:
            run_task_params["networkConfiguration"] = network_configuration

        response = self.ecs.run_task(**run_task_params)

        tasks = response["tasks"]

        if not tasks:
            failures = response["failures"]
            exceptions = []
            for failure in failures:
                arn = failure.get("arn")
                reason = failure.get("reason")
                detail = failure.get("detail")
                exceptions.append(Exception(f"Task {arn} failed because {reason}: {detail}"))
            raise Exception(exceptions)

        arn = tasks[0]["taskArn"]
        cluster_arn = tasks[0]["clusterArn"]
        self._set_run_tags(run.run_id, cluster=cluster_arn, task_arn=arn)
        self._set_ecs_tags(run.run_id, task_arn=arn)
        self.report_launch_events(run, arn, cluster_arn)

    def report_launch_events(
        self, run: PipelineRun, arn: Optional[str] = None, cluster: Optional[str] = None
    ):
        # Extracted method to allow for subclasses to customize the launch reporting behavior

        metadata_entries = []
        if arn:
            metadata_entries.append(MetadataEntry("ECS Task ARN", value=arn))
        if cluster:
            metadata_entries.append(MetadataEntry("ECS Cluster", value=cluster))

        metadata_entries.append(MetadataEntry("Run ID", value=run.run_id))
        self._instance.report_engine_event(
            message="Launching run in ECS task",
            pipeline_run=run,
            engine_event_data=EngineEventData(metadata_entries),
            cls=self.__class__,
        )

    def get_cpu_and_memory_overrides(self, run: PipelineRun) -> Dict[str, str]:
        overrides = {}

        cpu = run.tags.get("ecs/cpu")
        memory = run.tags.get("ecs/memory")

        if cpu:
            overrides["cpu"] = cpu
        if memory:
            overrides["memory"] = memory
        return overrides

    def _get_task_overrides(self, run: PipelineRun) -> Dict[str, Any]:
        overrides = run.tags.get("ecs/task_overrides")
        if overrides:
            return json.loads(overrides)
        return {}

    def terminate(self, run_id):
        tags = self._get_run_tags(run_id)

        if not (tags.arn and tags.cluster):
            return False

        tasks = self.ecs.describe_tasks(tasks=[tags.arn], cluster=tags.cluster).get("tasks")
        if not tasks:
            return False

        status = tasks[0].get("lastStatus")
        if status == "STOPPED":
            return False

        self.ecs.stop_task(task=tags.arn, cluster=tags.cluster)
        return True

    def _task_config(self, run, image, container_context) -> DagsterEcsTaskConfig:
        """
        Return a DagsterEcsTaskConfig to use to launch the ECS task, registering a new task
        definition if needed.
        """
        environment = self._environment(container_context)
        secrets = self._secrets(container_context)

        if self.task_definition:
            # Use the passed in task definition as a basis for the launched task (using the current
            # ECS task to determine network configuration and security groups)
            current_task_metadata = get_current_ecs_task_metadata()
            current_task = get_current_ecs_task(
                self.ecs, current_task_metadata.task_arn, current_task_metadata.cluster
            )
            task_definition = self.ecs.describe_task_definition(taskDefinition=self.task_definition)

            return get_task_config_from_current_task(
                self.ec2,
                current_task_metadata.cluster,
                current_task,
                task_definition["taskDefinition"]["family"],
            )

        family = sanitize_family(
            run.external_pipeline_origin.external_repository_origin.repository_location_origin.location_name  # type: ignore
        )

        if self.use_current_ecs_task:
            # Create a new task definition based on the launcher's task definition (re-using a
            # previous task with the same family if the configuration hasn't changed). Then
            # substitute in any configuration that was explicitly set on the run launcher
            current_task_metadata = get_current_ecs_task_metadata()
            current_task = get_current_ecs_task(
                self.ecs, current_task_metadata.task_arn, current_task_metadata.cluster
            )

            task_definition_dict = get_task_definition_dict_from_current_task(
                self.ecs,
                family,
                current_task,
                image,
                self.container_name,
                environment=environment,
                execution_role_arn=self.execution_role_arn,
                task_role_arn=self.task_role_arn,
                log_group=self.log_group,
                secrets=secrets if secrets else {},
                include_sidecars=self.include_sidecars,
                sidecar_container_definitions=self.sidecar_container_definitions,
            )

            task_definition_config = DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
                task_definition_dict,
                self.container_name,
            )

            if not self._reuse_task_definition(
                task_definition_config,
            ):
                self.ecs.register_task_definition(**task_definition_dict)

            return get_task_config_from_current_task(
                self.ec2,
                self.cluster or current_task_metadata.cluster,
                current_task,
                family,
                self.subnets,
                self.security_group_ids,
            )
        else:
            # Don't use the current task at all - purely derive the task to launch based on
            # the launcher config
            task_definition_config = DagsterEcsTaskDefinitionConfig(
                family=family,
                image=image,
                container_name=self.container_name,
                command=None,
                log_configuration={
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": self.log_group,
                        "awslogs-region": self.ecs.meta.region_name,
                        "awslogs-stream-prefix": family,
                    },
                },
                secrets=secrets,
                environment=environment,
                execution_role_arn=self.execution_role_arn,
                task_role_arn=self.task_role_arn,
                sidecars=self.sidecar_container_definitions,
            )
            if not self._reuse_task_definition(task_definition_config):
                task_definition_dict = task_definition_config.task_definition_dict(self.launch_type)
                # Register the task overridden task definition as a revision to the
                # "dagster-run" family.
                self.ecs.register_task_definition(**task_definition_dict)

            return DagsterEcsTaskConfig(
                task_definition=family,
                cluster=check.not_none(self.cluster),
                subnets=check.not_none(self.subnets),
                security_groups=self.security_group_ids,
                assign_public_ip=should_assign_public_ip(self.ec2, self.subnets),
                launch_type=self.launch_type,
            )

    def _reuse_task_definition(
        self, desired_task_definition_config: DagsterEcsTaskDefinitionConfig
    ):
        family = desired_task_definition_config.family

        try:
            existing_task_definition = self.ecs.describe_task_definition(taskDefinition=family)[
                "taskDefinition"
            ]
        except ClientError:
            # task definition does not exist, do not reuse
            return False

        existing_task_definition_config = DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
            existing_task_definition, self.container_name
        )

        return existing_task_definition_config == desired_task_definition_config

    def _environment(self, container_context):
        return [
            {"name": key, "value": value}
            for key, value in container_context.get_environment_dict().items()
        ]

    def _secrets(self, container_context):
        secrets = container_context.get_secrets_dict(self.secrets_manager)
        return (
            [{"name": key, "valueFrom": value} for key, value in secrets.items()] if secrets else []
        )

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, run: PipelineRun):

        tags = self._get_run_tags(run.run_id)

        if not (tags.arn and tags.cluster):
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, "")

        tasks = self.ecs.describe_tasks(tasks=[tags.arn], cluster=tags.cluster).get("tasks")
        if not tasks:
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, "")

        t = tasks[0]

        if t.get("lastStatus") in RUNNING_STATUSES:
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        elif t.get("lastStatus") in STOPPED_STATUSES:

            failed_containers = []
            for c in t.get("containers"):
                if c.get("exitCode") != 0:
                    failed_containers.append(c)
            if len(failed_containers) > 0:
                if len(failed_containers) > 1:
                    container_str = "Containers"
                else:
                    container_str = "Container"
                return CheckRunHealthResult(
                    WorkerStatus.FAILED,
                    f"ECS task failed. Stop code: {t.get('stopCode')}. Stop reason: {t.get('stoppedReason')}. "
                    f"{container_str} {[c.get('name') for c in failed_containers]} failed. "
                    f"Check the logs for task {t.get('taskArn')} for details.",
                )

            return CheckRunHealthResult(WorkerStatus.SUCCESS)

        return CheckRunHealthResult(WorkerStatus.UNKNOWN, "ECS task health status is unknown.")
