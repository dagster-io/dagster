from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, cast

from dagster import (
    Array,
    Field,
    Permissive,
    StringSource,
    _check as check,
)
from dagster._config import process_config
from dagster._core.container_context import process_shared_container_context_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.storage.dagster_run import DagsterRun

if TYPE_CHECKING:
    from dagster_docker import DockerRunLauncher

DOCKER_CONTAINER_CONTEXT_SCHEMA = {
    "registry": Field(
        {
            "url": Field(StringSource),
            "username": Field(StringSource),
            "password": Field(StringSource),
        },
        is_required=False,
        description="Information for using a non local/public docker registry",
    ),
    "env_vars": Field(
        [str],
        is_required=False,
        description=(
            "The list of environment variables names to include in the docker container. "
            "Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled "
            "from the local environment)"
        ),
    ),
    "container_kwargs": Field(
        Permissive(),
        is_required=False,
        description=(
            "key-value pairs that can be passed into containers.create. See "
            "https://docker-py.readthedocs.io/en/stable/containers.html for the full list "
            "of available options."
        ),
    ),
    "networks": Field(
        Array(StringSource),
        is_required=False,
        description=(
            "Names of the networks to which to connect the launched container at creation time"
        ),
    ),
}


class DockerContainerContext(
    NamedTuple(
        "_DockerContainerContext",
        [
            ("registry", Optional[Mapping[str, str]]),
            ("env_vars", Sequence[str]),
            ("networks", Sequence[str]),
            ("container_kwargs", Mapping[str, Any]),
        ],
    )
):
    """Encapsulates the configuration that can be applied to a Docker container running
    Dagster code. Can be set at the instance level (via config in the `DockerRunLauncher`),
    repository location level, and at the individual step level (for runs using the
    `docker_executor` to run each op in its own container). Config at each of these lower levels is
    merged in with any config set at a higher level, following the policy laid out in the
    merge() method below.
    """

    def __new__(
        cls,
        registry: Optional[Mapping[str, str]] = None,
        env_vars: Optional[Sequence[str]] = None,
        networks: Optional[Sequence[str]] = None,
        container_kwargs: Optional[Mapping[str, Any]] = None,
    ):
        return super().__new__(
            cls,
            registry=check.opt_nullable_mapping_param(registry, "registry"),
            env_vars=check.opt_sequence_param(env_vars, "env_vars", of_type=str),
            networks=check.opt_sequence_param(networks, "networks", of_type=str),
            container_kwargs=check.opt_mapping_param(container_kwargs, "container_kwargs"),
        )

    def merge(self, other: "DockerContainerContext"):
        # Combines config set at a higher level with overrides/additions that are set at a lower
        # level. For example, a certain set of config set in the `DockerRunLauncher`` can be
        # combined with config set at the step level in the `docker_executor`.
        # Lists of env vars and secrets are appended, the registry is replaced, and the
        # `container_kwargs` field does a shallow merge so that different kwargs can be combined
        # or replaced without replacing the full set of arguments.
        return DockerContainerContext(
            registry=other.registry if other.registry is not None else self.registry,
            env_vars=[*self.env_vars, *other.env_vars],
            networks=[*self.networks, *other.networks],
            container_kwargs={**self.container_kwargs, **other.container_kwargs},
        )

    @staticmethod
    def create_for_run(dagster_run: DagsterRun, run_launcher: Optional["DockerRunLauncher"]):
        context = DockerContainerContext()

        # First apply the instance / run_launcher-level context
        if run_launcher:
            context = context.merge(
                DockerContainerContext(
                    registry=run_launcher.registry,
                    env_vars=run_launcher.env_vars,
                    networks=run_launcher.networks,
                    container_kwargs=run_launcher.container_kwargs,
                )
            )

        run_container_context = (
            dagster_run.job_code_origin.repository_origin.container_context
            if dagster_run.job_code_origin
            else None
        )

        if not run_container_context:
            return context

        return context.merge(DockerContainerContext.create_from_config(run_container_context))

    @staticmethod
    def create_from_config(run_container_context):
        processed_shared_container_context = process_shared_container_context_config(
            run_container_context or {}
        )
        shared_container_context = DockerContainerContext(
            env_vars=processed_shared_container_context.get("env_vars", [])
        )

        run_docker_container_context = (
            run_container_context.get("docker", {}) if run_container_context else {}
        )

        if not run_docker_container_context:
            return shared_container_context

        processed_container_context = process_config(
            DOCKER_CONTAINER_CONTEXT_SCHEMA, run_docker_container_context
        )

        if not processed_container_context.success:
            raise DagsterInvalidConfigError(
                "Errors while parsing Docker container context",
                processed_container_context.errors,
                run_docker_container_context,
            )

        processed_context_value = cast(Mapping[str, Any], processed_container_context.value)

        return shared_container_context.merge(
            DockerContainerContext(
                registry=processed_context_value.get("registry"),
                env_vars=processed_context_value.get("env_vars", []),
                networks=processed_context_value.get("networks", []),
                container_kwargs=processed_context_value.get("container_kwargs"),
            )
        )
