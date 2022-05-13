from typing import TYPE_CHECKING, Any, List, Mapping, NamedTuple, Optional

from dagster import Array, Field, Noneable, Shape, StringSource
from dagster import _check as check
from dagster.config.validate import process_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils import merge_dicts

from ..secretsmanager import get_tagged_secrets

if TYPE_CHECKING:
    from . import EcsRunLauncher


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
    "environment": Field(
        Noneable(Array(Shape({"name": StringSource, "value": StringSource}))),
        is_required=False,
        description=(
            "An array of environment variables. These will be mounted as environment variables in "
            "the container. See "
            "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/taskdef-envfiles.html"
        ),
    ),
}


class EcsContainerContext(
    NamedTuple(
        "_EcsContainerContext",
        [("secrets", List[Any]), ("secrets_tags", List[str]), ("environment", List[Any])],
    )
):
    """Encapsulates configuration that can be applied to an ECS task running Dagster code."""

    def __new__(
        cls,
        secrets: Optional[List[Any]] = None,
        secrets_tags: Optional[List[str]] = None,
        environment: Optional[List[Any]] = None,
    ):
        return super(EcsContainerContext, cls).__new__(
            cls,
            secrets=check.opt_list_param(secrets, "secrets"),
            secrets_tags=check.opt_list_param(secrets_tags, "secrets_tags"),
            environment=check.opt_list_param(environment, "environment"),
        )

    def merge(self, other: "EcsContainerContext") -> "EcsContainerContext":

        new_secrets_keys = [s["name"] for s in other.secrets]
        merged_secrets = list(other.secrets)
        for s in self.secrets:
            if s["name"] not in new_secrets_keys:
                merged_secrets.append(s)

        new_env_keys = [e["name"] for e in other.environment]
        merged_env = list(other.environment)
        for e in self.environment:
            if e["name"] not in new_env_keys:
                merged_env.append(e)

        return EcsContainerContext(
            secrets=merged_secrets,
            secrets_tags=list(set(other.secrets_tags + self.secrets_tags)),
            environment=merged_env,
        )

    def get_secrets_dict(self, secrets_manager) -> Mapping[str, str]:
        return merge_dicts(
            (get_tagged_secrets(secrets_manager, self.secrets_tags) if self.secrets_tags else {}),
            {secret["name"]: secret["valueFrom"] for secret in self.secrets},
        )

    def get_environment_dict(self) -> Mapping[str, str]:
        return {env["name"]: env["value"] for env in self.environment}

    @staticmethod
    def create_for_run(pipeline_run: PipelineRun, run_launcher: Optional["EcsRunLauncher"]):
        context = EcsContainerContext()
        if run_launcher:
            context = context.merge(
                EcsContainerContext(
                    secrets=run_launcher.secrets,
                    secrets_tags=run_launcher.secrets_tags,
                    environment=run_launcher.environment,
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
    def create_from_config(run_container_context):
        run_ecs_container_context = (
            run_container_context.get("ecs", {}) if run_container_context else {}
        )

        if not run_ecs_container_context:
            return EcsContainerContext()

        processed_container_context = process_config(
            ECS_CONTAINER_CONTEXT_SCHEMA, run_ecs_container_context
        )

        if not processed_container_context.success:
            raise DagsterInvalidConfigError(
                "Errors while parsing ECS container context",
                processed_container_context.errors,
                run_ecs_container_context,
            )

        processed_context_value = processed_container_context.value

        return EcsContainerContext(
            secrets=processed_context_value.get("secrets"),
            secrets_tags=processed_context_value.get("secrets_tags"),
            environment=processed_context_value.get("environment"),
        )
