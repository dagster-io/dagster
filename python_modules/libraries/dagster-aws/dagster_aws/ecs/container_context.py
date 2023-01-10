from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Optional, Sequence, cast

from dagster import (
    Array,
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
from dagster._core.storage.pipeline_run import DagsterRun
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
            }
        )
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
            }
        )
    ),
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
            ("server_resources", Mapping[str, str]),
            ("run_resources", Mapping[str, str]),
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
    def create_for_run(pipeline_run: DagsterRun, run_launcher: Optional["EcsRunLauncher"]):
        context = EcsContainerContext()
        if run_launcher:
            context = context.merge(
                EcsContainerContext(
                    secrets=run_launcher.secrets,
                    secrets_tags=run_launcher.secrets_tags,
                    env_vars=run_launcher.env_vars,
                    task_definition_arn=run_launcher.task_definition,  # run launcher converts this from short name to ARN in constructor
                    run_resources=run_launcher.run_resources,
                )
            )

        run_container_context = (
            pipeline_run.pipeline_code_origin.repository_origin.container_context
            if pipeline_run.pipeline_code_origin
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
            )
        )
