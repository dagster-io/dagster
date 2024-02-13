from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Optional, Sequence, cast

from dagster import (
    Array,
    BoolSource,
    Field,
    Noneable,
    Permissive,
    Shape,
    StringSource,
    _check as check,
)
from dagster._config import process_config
from dagster._core.container_context import process_shared_container_context_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.utils import parse_env_var

from ..secretsmanager import get_tagged_secrets

if TYPE_CHECKING:
    from . import EcsRunLauncher

# Config shared between EcsRunLauncher and EcsContainerContext
SHARED_ECS_SCHEMA = {
    "env_vars": Field(
        [StringSource],
        is_required=False,
        description=(
            "List of environment variable names to include in the ECS task. "
            "Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled "
            "from the current process)"
        ),
    ),
    "run_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description="The CPU override to use for the launched task.",
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description="The memory override to use for the launched task.",
                ),
                "ephemeral_storage": Field(
                    int,
                    is_required=False,
                    description="The ephemeral storage, in GiB, to use for the launched task.",
                ),
            }
        )
    ),
    "run_ecs_tags": Field(
        Array(
            {
                "key": Field(StringSource, is_required=True),
                "value": Field(StringSource, is_required=False),
            }
        ),
        is_required=False,
        description="Additional tags to apply to the launched ECS task.",
    ),
}

SHARED_TASK_DEFINITION_FIELDS = {
    "execution_role_arn": Field(
        StringSource,
        is_required=False,
        description=(
            "ARN of the task execution role for the ECS container and Fargate agent to make AWS API"
            " calls on your behalf. See"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html. "
        ),
    ),
    "task_role_arn": Field(
        StringSource,
        is_required=False,
        description=(
            "ARN of the IAM role for launched tasks. See"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html. "
        ),
    ),
    "runtime_platform": Field(
        Shape(
            {
                "cpuArchitecture": Field(StringSource, is_required=False),
                "operatingSystemFamily": Field(StringSource, is_required=False),
            }
        ),
        is_required=False,
        description=(
            "The operating system that the task definition is running on. See"
            " https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.register_task_definition"
            " for the available options."
        ),
    ),
    "volumes": Field(
        Array(
            Permissive(
                {
                    "name": Field(StringSource, is_required=False),
                }
            )
        ),
        is_required=False,
        description=(
            "List of data volume definitions for the task. See"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html"
            " for the full list of available options."
        ),
    ),
    "mount_points": Field(
        Array(
            Shape(
                {
                    "sourceVolume": Field(StringSource, is_required=False),
                    "containerPath": Field(StringSource, is_required=False),
                    "readOnly": Field(BoolSource, is_required=False),
                }
            )
        ),
        is_required=False,
        description=(
            "Mount points for data volumes in the main container of the task."
            " See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html"
            " for more information."
        ),
    ),
    "repository_credentials": Field(
        StringSource,
        is_required=False,
        description=(
            "The arn of the secret to authenticate into your private container registry."
            " This does not apply if you are leveraging ECR for your images, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/userguide/private-auth.html."
        ),
    ),
}

ECS_CONTAINER_CONTEXT_SCHEMA = {
    "secrets": Field(
        Noneable(Array(Shape({"name": StringSource, "valueFrom": StringSource}))),
        is_required=False,
        description=(
            "An array of AWS Secrets Manager secrets. These secrets will "
            "be mounted as environment variables in the container. See "
            "https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html."
        ),
    ),
    "secrets_tags": Field(
        Noneable(Array(StringSource)),
        is_required=False,
        description=(
            "AWS Secrets Manager secrets with these tags will be mounted as "
            "environment variables in the container."
        ),
    ),
    "task_definition_arn": Field(
        StringSource,
        is_required=False,
        description="ARN of the task definition to use to launch the container.",
    ),
    "container_name": Field(
        StringSource,
        is_required=False,
        description="Name of the container in the task definition to use to run Dagster code.",
    ),
    "server_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description="The CPU override to use for the launched task.",
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description="The memory override to use for the launched task.",
                ),
                "ephemeral_storage": Field(
                    int,
                    is_required=False,
                    description="The ephemeral storage, in GiB, to use for the launched task.",
                ),
            }
        )
    ),
    "server_sidecar_containers": Field(
        Array(Permissive({})),
        is_required=False,
        description="Additional sidecar containers to include in code server task definitions.",
    ),
    "server_ecs_tags": Field(
        Array(
            {
                "key": Field(StringSource, is_required=True),
                "value": Field(StringSource, is_required=False),
            }
        ),
        is_required=False,
        description="Additional tags to apply to the launched ECS task for a code server.",
    ),
    "run_sidecar_containers": Field(
        Array(Permissive({})),
        is_required=False,
        description="Additional sidecar containers to include in run task definitions.",
    ),
    **SHARED_TASK_DEFINITION_FIELDS,
    **SHARED_ECS_SCHEMA,
}


class EcsContainerContext(
    NamedTuple(
        "_EcsContainerContext",
        [
            ("secrets", Sequence[Any]),
            ("secrets_tags", Sequence[str]),
            ("env_vars", Sequence[str]),
            ("task_definition_arn", Optional[str]),
            ("container_name", Optional[str]),
            ("server_resources", Mapping[str, Any]),
            ("run_resources", Mapping[str, Any]),
            ("task_role_arn", Optional[str]),
            ("execution_role_arn", Optional[str]),
            ("runtime_platform", Mapping[str, Any]),
            ("mount_points", Sequence[Mapping[str, Any]]),
            ("volumes", Sequence[Mapping[str, Any]]),
            ("server_sidecar_containers", Sequence[Mapping[str, Any]]),
            ("run_sidecar_containers", Sequence[Mapping[str, Any]]),
            ("server_ecs_tags", Sequence[Mapping[str, Optional[str]]]),
            ("run_ecs_tags", Sequence[Mapping[str, Optional[str]]]),
            ("repository_credentials", Optional[str]),
        ],
    )
):
    """Encapsulates configuration that can be applied to an ECS task running Dagster code."""

    def __new__(
        cls,
        secrets: Optional[Sequence[Any]] = None,
        secrets_tags: Optional[Sequence[str]] = None,
        env_vars: Optional[Sequence[str]] = None,
        task_definition_arn: Optional[str] = None,
        container_name: Optional[str] = None,
        server_resources: Optional[Mapping[str, str]] = None,
        run_resources: Optional[Mapping[str, str]] = None,
        task_role_arn: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        runtime_platform: Optional[Mapping[str, Any]] = None,
        mount_points: Optional[Sequence[Mapping[str, Any]]] = None,
        volumes: Optional[Sequence[Mapping[str, Any]]] = None,
        server_sidecar_containers: Optional[Sequence[Mapping[str, Any]]] = None,
        run_sidecar_containers: Optional[Sequence[Mapping[str, Any]]] = None,
        server_ecs_tags: Optional[Sequence[Mapping[str, Optional[str]]]] = None,
        run_ecs_tags: Optional[Sequence[Mapping[str, Optional[str]]]] = None,
        repository_credentials: Optional[str] = None,
    ):
        return super(EcsContainerContext, cls).__new__(
            cls,
            secrets=check.opt_sequence_param(secrets, "secrets"),
            secrets_tags=check.opt_sequence_param(secrets_tags, "secrets_tags"),
            env_vars=check.opt_sequence_param(env_vars, "env_vars"),
            task_definition_arn=check.opt_str_param(task_definition_arn, "task_definition_arn"),
            container_name=check.opt_str_param(container_name, "container_name"),
            server_resources=check.opt_mapping_param(server_resources, "server_resources"),
            run_resources=check.opt_mapping_param(run_resources, "run_resources"),
            task_role_arn=check.opt_str_param(task_role_arn, "task_role_arn"),
            execution_role_arn=check.opt_str_param(execution_role_arn, "execution_role_arn"),
            runtime_platform=check.opt_mapping_param(
                runtime_platform, "runtime_platform", key_type=str
            ),
            mount_points=check.opt_sequence_param(mount_points, "mount_points"),
            volumes=check.opt_sequence_param(volumes, "volumes"),
            server_sidecar_containers=check.opt_sequence_param(
                server_sidecar_containers, "server_sidecar_containers"
            ),
            run_sidecar_containers=check.opt_sequence_param(
                run_sidecar_containers, "run_sidecar_containers"
            ),
            server_ecs_tags=check.opt_sequence_param(server_ecs_tags, "server_ecs_tags"),
            run_ecs_tags=check.opt_sequence_param(run_ecs_tags, "run_tags"),
            repository_credentials=check.opt_str_param(
                repository_credentials, "repository_credentials"
            ),
        )

    def merge(self, other: "EcsContainerContext") -> "EcsContainerContext":
        return EcsContainerContext(
            secrets=[*other.secrets, *self.secrets],
            secrets_tags=[*other.secrets_tags, *self.secrets_tags],
            env_vars=[*other.env_vars, *self.env_vars],
            task_definition_arn=other.task_definition_arn or self.task_definition_arn,
            container_name=other.container_name or self.container_name,
            server_resources={**self.server_resources, **other.server_resources},
            run_resources={**self.run_resources, **other.run_resources},
            task_role_arn=other.task_role_arn or self.task_role_arn,
            execution_role_arn=other.execution_role_arn or self.execution_role_arn,
            runtime_platform=other.runtime_platform or self.runtime_platform,
            mount_points=[*other.mount_points, *self.mount_points],
            volumes=[*other.volumes, *self.volumes],
            server_sidecar_containers=[
                *other.server_sidecar_containers,
                *self.server_sidecar_containers,
            ],
            run_sidecar_containers=[*other.run_sidecar_containers, *self.run_sidecar_containers],
            server_ecs_tags=[*other.server_ecs_tags, *self.server_ecs_tags],
            run_ecs_tags=[*other.run_ecs_tags, *self.run_ecs_tags],
            repository_credentials=other.repository_credentials or self.repository_credentials,
        )

    def get_secrets_dict(self, secrets_manager) -> Mapping[str, str]:
        return {
            **(get_tagged_secrets(secrets_manager, self.secrets_tags) if self.secrets_tags else {}),
            **{secret["name"]: secret["valueFrom"] for secret in self.secrets},
        }

    def get_environment_dict(self) -> Mapping[str, str]:
        parsed_env_var_tuples = [parse_env_var(env_var) for env_var in self.env_vars]
        return {env_var_tuple[0]: env_var_tuple[1] for env_var_tuple in parsed_env_var_tuples}

    @staticmethod
    def create_for_run(dagster_run: DagsterRun, run_launcher: Optional["EcsRunLauncher[Any]"]):
        context = EcsContainerContext()
        if run_launcher:
            context = context.merge(
                EcsContainerContext(
                    secrets=run_launcher.secrets,
                    secrets_tags=run_launcher.secrets_tags,
                    env_vars=run_launcher.env_vars,
                    task_definition_arn=run_launcher.task_definition,  # run launcher converts this from short name to ARN in constructor
                    run_resources=run_launcher.run_resources,
                    task_role_arn=run_launcher.task_role_arn,
                    execution_role_arn=run_launcher.execution_role_arn,
                    runtime_platform=run_launcher.runtime_platform,
                    mount_points=run_launcher.mount_points,
                    volumes=run_launcher.volumes,
                    run_sidecar_containers=run_launcher.run_sidecar_containers,
                    run_ecs_tags=run_launcher.run_ecs_tags,
                    repository_credentials=run_launcher.repository_credentials,
                )
            )

        run_container_context = (
            dagster_run.job_code_origin.repository_origin.container_context
            if dagster_run.job_code_origin
            else None
        )

        if not run_container_context:
            return context

        return context.merge(EcsContainerContext.create_from_config(run_container_context))

    @staticmethod
    def create_from_config(run_container_context) -> "EcsContainerContext":
        processed_shared_container_context = process_shared_container_context_config(
            run_container_context or {}
        )
        shared_container_context = EcsContainerContext(
            env_vars=processed_shared_container_context.get("env_vars", [])
        )

        run_ecs_container_context = (
            run_container_context.get("ecs", {}) if run_container_context else {}
        )

        if not run_ecs_container_context:
            return shared_container_context

        processed_container_context = process_config(
            ECS_CONTAINER_CONTEXT_SCHEMA, run_ecs_container_context
        )

        if not processed_container_context.success:
            raise DagsterInvalidConfigError(
                "Errors while parsing ECS container context",
                processed_container_context.errors,
                run_ecs_container_context,
            )

        processed_context_value = cast(Mapping[str, Any], processed_container_context.value)

        return shared_container_context.merge(
            EcsContainerContext(
                secrets=processed_context_value.get("secrets"),
                secrets_tags=processed_context_value.get("secrets_tags"),
                env_vars=processed_context_value.get("env_vars"),
                task_definition_arn=processed_context_value.get("task_definition_arn"),
                container_name=processed_context_value.get("container_name"),
                server_resources=processed_context_value.get("server_resources"),
                run_resources=processed_context_value.get("run_resources"),
                task_role_arn=processed_context_value.get("task_role_arn"),
                execution_role_arn=processed_context_value.get("execution_role_arn"),
                runtime_platform=processed_context_value.get("runtime_platform"),
                mount_points=processed_context_value.get("mount_points"),
                volumes=processed_context_value.get("volumes"),
                server_sidecar_containers=processed_context_value.get("server_sidecar_containers"),
                run_sidecar_containers=processed_context_value.get("run_sidecar_containers"),
                server_ecs_tags=processed_context_value.get("server_ecs_tags"),
                run_ecs_tags=processed_context_value.get("run_ecs_tags"),
                repository_credentials=processed_context_value.get("repository_credentials"),
            )
        )
