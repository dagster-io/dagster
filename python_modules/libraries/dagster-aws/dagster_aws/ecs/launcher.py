import json
import logging
import os
import uuid
import warnings
from collections import namedtuple
from typing import Any, Dict, List, Mapping, Optional, Sequence

import boto3
from botocore.exceptions import ClientError
from dagster import (
    Array,
    DagsterRunStatus,
    Field,
    Noneable,
    Permissive,
    ScalarUnion,
    StringSource,
    _check as check,
)
from dagster._core.events import EngineEventData
from dagster._core.instance import T_DagsterInstance
from dagster._core.launcher.base import (
    CheckRunHealthResult,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import RUN_WORKER_ID_TAG
from dagster._grpc.types import ExecuteRunArgs
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils.backoff import backoff
from typing_extensions import Self

from ..secretsmanager import get_secrets_from_arns
from .container_context import SHARED_ECS_SCHEMA, SHARED_TASK_DEFINITION_FIELDS, EcsContainerContext
from .tasks import (
    DagsterEcsTaskDefinitionConfig,
    get_current_ecs_task,
    get_current_ecs_task_metadata,
    get_task_definition_dict_from_current_task,
    get_task_kwargs_from_current_task,
)
from .utils import get_task_definition_family, get_task_logs, task_definitions_match

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

DEFAULT_WINDOWS_RESOURCES = {"cpu": "1024", "memory": "2048"}

DEFAULT_LINUX_RESOURCES = {"cpu": "256", "memory": "512"}


class EcsRunLauncher(RunLauncher[T_DagsterInstance], ConfigurableClass):
    """RunLauncher that starts a task in ECS for each Dagster job run."""

    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
        task_definition=None,
        container_name="run",
        secrets=None,
        secrets_tag="dagster",
        env_vars=None,
        include_sidecars=False,
        use_current_ecs_task_config: bool = True,
        run_task_kwargs: Optional[Mapping[str, Any]] = None,
        run_resources: Optional[Dict[str, Any]] = None,
        run_ecs_tags: Optional[List[Dict[str, Optional[str]]]] = None,
    ):
        self._inst_data = inst_data
        self.ecs = boto3.client("ecs")
        self.ec2 = boto3.resource("ec2")
        self.secrets_manager = boto3.client("secretsmanager")
        self.logs = boto3.client("logs")

        self.task_definition = None
        self.task_definition_dict = {}
        if isinstance(task_definition, str):
            self.task_definition = task_definition
        elif task_definition and "env" in task_definition:
            check.invariant(
                len(task_definition) == 1,
                "If `task_definition` is set to a dictionary with `env`, `env` must be the only"
                " key.",
            )
            env_var = task_definition["env"]
            self.task_definition = os.getenv(env_var)
            if not self.task_definition:
                raise Exception(
                    f"You have attempted to fetch the environment variable {env_var} which is not"
                    " set."
                )
        else:
            self.task_definition_dict = task_definition or {}

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

        if self.task_definition:
            task_definition = self.ecs.describe_task_definition(taskDefinition=self.task_definition)
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

        self.use_current_ecs_task_config = check.opt_bool_param(
            use_current_ecs_task_config, "use_current_ecs_task_config"
        )

        self.run_task_kwargs = check.opt_mapping_param(run_task_kwargs, "run_task_kwargs")
        if run_task_kwargs:
            check.invariant(
                "taskDefinition" not in run_task_kwargs,
                "Use the `taskDefinition` config field to pass in a task definition to run.",
            )
            check.invariant(
                "overrides" not in run_task_kwargs,
                "Task overrides are set by the run launcher and cannot be set in run_task_kwargs.",
            )

            expected_keys = [
                key for key in self.ecs.meta.service_model.shape_for("RunTaskRequest").members
            ]

            for key in run_task_kwargs:
                check.invariant(
                    key in expected_keys, f"Found an unexpected key {key} in run_task_kwargs"
                )

        self.run_resources = check.opt_mapping_param(run_resources, "run_resources")

        self.run_ecs_tags = check.opt_sequence_param(run_ecs_tags, "run_ecs_tags")

        self._current_task_metadata = None
        self._current_task = None

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def task_role_arn(self) -> Optional[str]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("task_role_arn")

    @property
    def execution_role_arn(self) -> Optional[str]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("execution_role_arn")

    @property
    def runtime_platform(self) -> Optional[Mapping[str, Any]]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("runtime_platform")

    @property
    def mount_points(self) -> Optional[Sequence[Mapping[str, Any]]]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("mount_points")

    @property
    def volumes(self) -> Optional[Sequence[Mapping[str, Any]]]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("volumes")

    @property
    def repository_credentials(self) -> Optional[str]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("repository_credentials")

    @property
    def run_sidecar_containers(self) -> Optional[Sequence[Mapping[str, Any]]]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("sidecar_containers")

    @property
    def linux_parameters(self) -> Optional[Mapping[str, Any]]:
        if not self.task_definition_dict:
            return None
        return self.task_definition_dict.get("linux_parameters")

    @classmethod
    def config_type(cls):
        return {
            "task_definition": Field(
                ScalarUnion(
                    scalar_type=str,
                    non_scalar_schema={
                        "log_group": Field(StringSource, is_required=False),
                        "sidecar_containers": Field(Array(Permissive({})), is_required=False),
                        "requires_compatibilities": Field(Array(str), is_required=False),
                        "env": Field(
                            str,
                            is_required=False,
                            description=(
                                "Backwards-compatibility for when task_definition was a"
                                " StringSource.Can be used to source the task_definition scalar"
                                " from an environment variable."
                            ),
                        ),
                        "linux_parameters": Field(Permissive(), is_required=False),
                        **SHARED_TASK_DEFINITION_FIELDS,
                    },
                ),
                is_required=False,
                description=(
                    "Either the short name of an existing task definition to use when launching new"
                    " tasks, or a dictionary configuration to use when creating a task definition"
                    " for the run.If neither is provided, the task definition will be created based"
                    " on the current task's task definition."
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
            "use_current_ecs_task_config": Field(
                bool,
                is_required=False,
                default_value=True,
                description=(
                    "Whether to use the run launcher's current ECS task in order to determine "
                    "the cluster and networking configuration for the launched task. Defaults to "
                    "True. Should only be called if the run launcher is running within an ECS "
                    "task."
                ),
            ),
            "run_task_kwargs": Field(
                Permissive(
                    {
                        "cluster": Field(
                            StringSource,
                            is_required=False,
                            description="Name of the ECS cluster to launch ECS tasks in.",
                        ),
                    }
                ),
                is_required=False,
                description=(
                    "Additional arguments to include while running the task. See"
                    " https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task"
                    " for the available parameters. The overrides and taskDefinition arguments will"
                    " always be set by the run launcher."
                ),
            ),
            **SHARED_ECS_SCHEMA,
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    def _set_run_tags(self, run_id: str, cluster: str, task_arn: str):
        tags = {
            "ecs/task_arn": task_arn,
            "ecs/cluster": cluster,
            RUN_WORKER_ID_TAG: str(uuid.uuid4().hex)[0:6],
        }
        self._instance.add_run_tags(run_id, tags)

    def build_ecs_tags_for_run_task(self, run, container_context: EcsContainerContext):
        if any(tag["key"] == "dagster/run_id" for tag in container_context.run_ecs_tags):
            raise Exception("Cannot override system ECS tag: dagster/run_id")

        return [{"key": "dagster/run_id", "value": run.run_id}, *container_context.run_ecs_tags]

    def _get_run_tags(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        tags = run.tags if run else {}
        arn = tags.get("ecs/task_arn")
        cluster = tags.get("ecs/cluster")
        cpu = tags.get("ecs/cpu")
        memory = tags.get("ecs/memory")

        return Tags(arn, cluster, cpu, memory)

    def _get_command_args(self, run_args: ExecuteRunArgs, context: LaunchRunContext):
        return run_args.get_command_args()

    def _get_image_for_run(self, context: LaunchRunContext) -> Optional[str]:
        job_origin = check.not_none(context.job_code_origin)
        return job_origin.repository_origin.container_image

    def launch_run(self, context: LaunchRunContext) -> None:
        """Launch a run in an ECS task."""
        run = context.dagster_run
        container_context = EcsContainerContext.create_for_run(run, self)

        job_origin = check.not_none(context.job_code_origin)

        # ECS limits overrides to 8192 characters including json formatting
        # https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RunTask.html
        # When container_context is serialized as part of the ExecuteRunArgs, we risk
        # going over this limit (for example, if many secrets have been set). This strips
        # the container context off of our job origin because we don't actually need
        # it to launch the run; we only needed it to create the task definition.
        repository_origin = job_origin.repository_origin

        stripped_repository_origin = repository_origin._replace(container_context={})
        stripped_job_origin = job_origin._replace(repository_origin=stripped_repository_origin)

        args = ExecuteRunArgs(
            job_origin=stripped_job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
        )
        command = self._get_command_args(args, context)
        image = self._get_image_for_run(context)

        run_task_kwargs = self._run_task_kwargs(run, image, container_context)

        # Set cpu or memory overrides
        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
        cpu_and_memory_overrides = self.get_cpu_and_memory_overrides(container_context, run)

        task_overrides = self._get_task_overrides(container_context, run)

        container_overrides: List[Dict[str, Any]] = [
            {
                "name": self._get_container_name(container_context),
                "command": command,
                # containerOverrides expects cpu/memory as integers
                **{k: int(v) for k, v in cpu_and_memory_overrides.items()},
            }
        ]

        run_task_kwargs["overrides"] = {
            "containerOverrides": container_overrides,
            # taskOverrides expects cpu/memory as strings
            **cpu_and_memory_overrides,
            **task_overrides,
        }
        run_task_kwargs["tags"] = [
            *run_task_kwargs.get("tags", []),
            *self.build_ecs_tags_for_run_task(run, container_context),
        ]

        run_task_kwargs_from_run = self._get_run_task_kwargs_from_run(run)
        run_task_kwargs.update(run_task_kwargs_from_run)

        # launchType and capacityProviderStrategy are incompatible - prefer the latter if it is set
        if "launchType" in run_task_kwargs and run_task_kwargs.get("capacityProviderStrategy"):
            del run_task_kwargs["launchType"]

        # Run a task using the same network configuration as this processes's task.
        response = self.ecs.run_task(**run_task_kwargs)

        tasks = response["tasks"]

        if not tasks:
            failures = response["failures"]
            failure_messages = []
            for failure in failures:
                arn = failure.get("arn")
                reason = failure.get("reason")
                detail = failure.get("detail")

                failure_message = (
                    "Task"
                    + (f" {arn}" if arn else "")
                    + " failed."
                    + (f" Failure reason: {reason}" if reason else "")
                    + (f" Failure details: {detail}" if detail else "")
                )
                failure_messages.append(failure_message)

            raise Exception("\n".join(failure_messages) if failure_messages else "Task failed.")

        arn = tasks[0]["taskArn"]
        cluster_arn = tasks[0]["clusterArn"]
        self._set_run_tags(run.run_id, cluster=cluster_arn, task_arn=arn)
        self.report_launch_events(run, arn, cluster_arn)

    def report_launch_events(
        self, run: DagsterRun, arn: Optional[str] = None, cluster: Optional[str] = None
    ):
        # Extracted method to allow for subclasses to customize the launch reporting behavior

        metadata = {}
        if arn:
            metadata["ECS Task ARN"] = arn
        if cluster:
            metadata["ECS Cluster"] = cluster

        metadata["Run ID"] = run.run_id
        self._instance.report_engine_event(
            message="Launching run in ECS task",
            dagster_run=run,
            engine_event_data=EngineEventData(metadata),
            cls=self.__class__,
        )

    def get_cpu_and_memory_overrides(
        self, container_context: EcsContainerContext, run: DagsterRun
    ) -> Mapping[str, str]:
        overrides = {}

        cpu = run.tags.get("ecs/cpu", container_context.run_resources.get("cpu"))
        memory = run.tags.get("ecs/memory", container_context.run_resources.get("memory"))

        if cpu:
            overrides["cpu"] = cpu
        if memory:
            overrides["memory"] = memory

        return overrides

    def _get_task_overrides(
        self, container_context: EcsContainerContext, run: DagsterRun
    ) -> Mapping[str, Any]:
        tag_overrides = run.tags.get("ecs/task_overrides")

        overrides = {}

        if tag_overrides:
            overrides = json.loads(tag_overrides)

        ephemeral_storage = run.tags.get(
            "ecs/ephemeral_storage", container_context.run_resources.get("ephemeral_storage")
        )
        if ephemeral_storage:
            overrides["ephemeralStorage"] = {"sizeInGiB": int(ephemeral_storage)}

        return overrides

    def _get_run_task_kwargs_from_run(self, run: DagsterRun) -> Mapping[str, Any]:
        run_task_kwargs = run.tags.get("ecs/run_task_kwargs")
        if run_task_kwargs:
            return json.loads(run_task_kwargs)
        return {}

    def terminate(self, run_id):
        tags = self._get_run_tags(run_id)

        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False

        self._instance.report_run_canceling(run)

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

    def _get_current_task_metadata(self):
        if self._current_task_metadata is None:
            self._current_task_metadata = get_current_ecs_task_metadata()
        return self._current_task_metadata

    def _get_current_task(self):
        if self._current_task is None:
            current_task_metadata = self._get_current_task_metadata()
            self._current_task = get_current_ecs_task(
                self.ecs, current_task_metadata.task_arn, current_task_metadata.cluster
            )

        return self._current_task

    def _get_run_task_definition_family(self, run: DagsterRun) -> str:
        return get_task_definition_family("run", check.not_none(run.external_job_origin))

    def _get_container_name(self, container_context) -> str:
        return container_context.container_name or self.container_name

    def _run_task_kwargs(self, run, image, container_context) -> Dict[str, Any]:
        """Return a dictionary of args to launch the ECS task, registering a new task
        definition if needed.
        """
        environment = self._environment(container_context)
        environment.append({"name": "DAGSTER_RUN_JOB_NAME", "value": run.job_name})

        secrets = self._secrets(container_context)

        if container_context.task_definition_arn:
            task_definition = container_context.task_definition_arn
        else:
            family = self._get_run_task_definition_family(run)

            if self.task_definition_dict or not self.use_current_ecs_task_config:
                runtime_platform = container_context.runtime_platform
                is_windows = container_context.runtime_platform.get(
                    "operatingSystemFamily"
                ) not in {None, "LINUX"}

                default_resources = (
                    DEFAULT_WINDOWS_RESOURCES if is_windows else DEFAULT_LINUX_RESOURCES
                )
                task_definition_config = DagsterEcsTaskDefinitionConfig(
                    family,
                    image,
                    self._get_container_name(container_context),
                    command=None,
                    log_configuration=(
                        {
                            "logDriver": "awslogs",
                            "options": {
                                "awslogs-group": self.task_definition_dict["log_group"],
                                "awslogs-region": self.ecs.meta.region_name,
                                "awslogs-stream-prefix": family,
                            },
                        }
                        if self.task_definition_dict.get("log_group")
                        else None
                    ),
                    secrets=secrets if secrets else [],
                    environment=environment,
                    execution_role_arn=container_context.execution_role_arn,
                    task_role_arn=container_context.task_role_arn,
                    sidecars=container_context.run_sidecar_containers,
                    requires_compatibilities=self.task_definition_dict.get(
                        "requires_compatibilities", []
                    ),
                    cpu=container_context.run_resources.get("cpu", default_resources["cpu"]),
                    memory=container_context.run_resources.get(
                        "memory", default_resources["memory"]
                    ),
                    ephemeral_storage=container_context.run_resources.get("ephemeral_storage"),
                    runtime_platform=runtime_platform,
                    volumes=container_context.volumes,
                    mount_points=container_context.mount_points,
                    repository_credentials=container_context.repository_credentials,
                    linux_parameters=self.linux_parameters,
                )
                task_definition_dict = task_definition_config.task_definition_dict()
            else:
                task_definition_dict = get_task_definition_dict_from_current_task(
                    self.ecs,
                    family,
                    self._get_current_task(),
                    image,
                    self._get_container_name(container_context),
                    environment=environment,
                    secrets=secrets if secrets else {},
                    include_sidecars=self.include_sidecars,
                    task_role_arn=container_context.task_role_arn,
                    execution_role_arn=container_context.execution_role_arn,
                    cpu=container_context.run_resources.get("cpu"),
                    memory=container_context.run_resources.get("memory"),
                    runtime_platform=container_context.runtime_platform,
                    ephemeral_storage=container_context.run_resources.get("ephemeral_storage"),
                    volumes=container_context.volumes,
                    mount_points=container_context.mount_points,
                    additional_sidecars=container_context.run_sidecar_containers,
                    repository_credentials=container_context.repository_credentials,
                )

                task_definition_config = DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
                    task_definition_dict,
                    self._get_container_name(container_context),
                )

            container_name = self._get_container_name(container_context)

            backoff(
                self._reuse_or_register_task_definition,
                retry_on=(Exception,),
                kwargs={
                    "desired_task_definition_config": task_definition_config,
                    "container_name": container_name,
                    "task_definition_dict": task_definition_dict,
                },
                max_retries=5,
            )

            task_definition = family

        if self.use_current_ecs_task_config:
            current_task_metadata = get_current_ecs_task_metadata()
            current_task = get_current_ecs_task(
                self.ecs, current_task_metadata.task_arn, current_task_metadata.cluster
            )
            task_kwargs = get_task_kwargs_from_current_task(
                self.ec2,
                current_task_metadata.cluster,
                current_task,
            )
        else:
            task_kwargs = {}

        return {**task_kwargs, **self.run_task_kwargs, "taskDefinition": task_definition}

    def _reuse_task_definition(
        self, desired_task_definition_config: DagsterEcsTaskDefinitionConfig, container_name: str
    ):
        family = desired_task_definition_config.family

        try:
            existing_task_definition = self.ecs.describe_task_definition(taskDefinition=family)[
                "taskDefinition"
            ]
        except ClientError:
            # task definition does not exist, do not reuse
            return False

        return task_definitions_match(
            desired_task_definition_config,
            existing_task_definition,
            container_name=container_name,
        )

    def _reuse_or_register_task_definition(
        self,
        desired_task_definition_config: DagsterEcsTaskDefinitionConfig,
        container_name: str,
        task_definition_dict: dict,
    ):
        if not self._reuse_task_definition(desired_task_definition_config, container_name):
            self.ecs.register_task_definition(**task_definition_dict)

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

    @property
    def include_cluster_info_in_failure_messages(self):
        return True

    def _is_transient_stop_reason(self, stopped_reason: str):
        if "Timeout waiting for network interface provisioning to complete" in stopped_reason:
            return True

        if "Timeout waiting for EphemeralStorage provisioning to complete" in stopped_reason:
            return True

        if "CannotPullContainerError" in stopped_reason and "i/o timeout" in stopped_reason:
            return True

        return False

    def _is_transient_startup_failure(self, run, task):
        if not task.get("stoppedReason"):
            return False
        return run.status == DagsterRunStatus.STARTING and self._is_transient_stop_reason(
            task.get("stoppedReason")
        )

    def check_run_worker_health(self, run: DagsterRun):
        run_worker_id = run.tags.get(RUN_WORKER_ID_TAG)

        tags = self._get_run_tags(run.run_id)
        container_context = EcsContainerContext.create_for_run(run, self)

        if not (tags.arn and tags.cluster):
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, "", run_worker_id=run_worker_id)

        tasks = self.ecs.describe_tasks(tasks=[tags.arn], cluster=tags.cluster).get("tasks")
        if not tasks:
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, "", run_worker_id=run_worker_id)

        t = tasks[0]

        if t.get("lastStatus") in RUNNING_STATUSES:
            return CheckRunHealthResult(WorkerStatus.RUNNING, run_worker_id=run_worker_id)
        elif t.get("lastStatus") in STOPPED_STATUSES:
            failed_containers = []
            for c in t.get("containers"):
                if c.get("exitCode") != 0:
                    failed_containers.append(c)
            if len(failed_containers) > 0:
                failure_text = ""

                cluster_failure_info = (
                    f"Task {t.get('taskArn')} failed.\n"
                    f"Stop code: {t.get('stopCode')}.\n"
                    f"Stop reason: {t.get('stoppedReason')}.\n"
                )
                for c in failed_containers:
                    exit_code = c.get("exitCode")
                    exit_code_msg = f" - exit code {exit_code}" if exit_code is not None else ""
                    cluster_failure_info += f"Container '{c.get('name')}' failed{exit_code_msg}.\n"

                logging.warning(
                    "Run monitoring detected run worker failure: " + cluster_failure_info
                )

                if self.include_cluster_info_in_failure_messages:
                    failure_text += cluster_failure_info

                logs = []

                try:
                    logs = get_task_logs(
                        self.ecs,
                        logs_client=self.logs,
                        cluster=tags.cluster,
                        task_arn=tags.arn,
                        container_name=self._get_container_name(container_context),
                    )
                except:
                    logging.exception(f"Error trying to get logs for failed task {tags.arn}")

                if logs:
                    failure_text += "Run worker logs:\n" + "\n".join(logs)

                return CheckRunHealthResult(
                    WorkerStatus.FAILED,
                    failure_text,
                    transient=self._is_transient_startup_failure(run, t),
                    run_worker_id=run_worker_id,
                )

            return CheckRunHealthResult(WorkerStatus.SUCCESS, run_worker_id=run_worker_id)

        return CheckRunHealthResult(
            WorkerStatus.UNKNOWN, "ECS task health status is unknown.", run_worker_id=run_worker_id
        )
