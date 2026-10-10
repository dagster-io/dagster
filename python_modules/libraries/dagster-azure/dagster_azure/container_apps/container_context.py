from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from dagster import (
    Field,
    Permissive,
    StringSource,
    _check as check,
)
from dagster._config import process_config
from dagster._core.container_context.config import process_shared_container_context_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.utils import parse_env_var

if TYPE_CHECKING:
    from dagster._core.storage.dagster_run import DagsterRun

    from dagster_azure.container_apps.launcher import AcaRunLauncher


SHARED_ACA_SCHEMA: dict[str, Field] = {
    "env_vars": Field(
        [StringSource],
        is_required=False,
        description=(
            "Environment variable names to forward to the ACA Job. "
            "Entries of the form KEY=VALUE set the value literally; a bare KEY "
            "inherits from the current process's environment."
        ),
    ),
    "run_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description='CPU for the run container (decimal cores or millicpus, e.g. "0.5" or "500m").',
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description='Memory for the run container (e.g. "1Gi", "512Mi").',
                ),
            }
        ),
        is_required=False,
    ),
    "run_job_replica_timeout": Field(
        int,
        is_required=False,
        description=(
            "How long ACA allows the Job's single replica to run before "
            "forcibly terminating it, in seconds. Azure requires a value; when "
            "unset here and on the code location, the run launcher uses 24 hours."
        ),
    ),
    "server_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description='CPU for the code server container (e.g. "0.5" or "500m").',
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description='Memory for the code server container (e.g. "1Gi").',
                ),
            }
        ),
        is_required=False,
        description=(
            "Resource overrides applied when the ACA primitive is used for "
            "long-lived code servers (consumed by the dagster-cloud user code "
            "launcher). Ignored by the run launcher."
        ),
    ),
    "identity_id": Field(
        StringSource,
        is_required=False,
        description=(
            "Full ARM resource ID of a user-assigned managed identity to attach to the "
            "launched Job. ACA Jobs and Container Apps use this identity to pull images "
            "from Azure Container Registry — no registry credentials are stored on the "
            "agent. If unset, the Job runs with the system-assigned identity (if enabled "
            "on the environment)."
        ),
    ),
}

ACA_CONTAINER_CONTEXT_SCHEMA: dict[str, Field] = {**SHARED_ACA_SCHEMA}


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


class AcaContainerContext(
    NamedTuple(
        "_AcaContainerContext",
        [
            ("env_vars", Sequence[str]),
            ("run_resources", Mapping[str, Any]),
            ("server_resources", Mapping[str, Any]),
            ("identity_id", str | None),
            ("run_job_replica_timeout", int | None),
        ],
    )
):
    """Container context for Azure Container Apps Jobs."""

    def __new__(
        cls,
        *,
        env_vars: Sequence[str] | None,
        run_resources: Mapping[str, Any] | None,
        server_resources: Mapping[str, Any] | None,
        identity_id: str | None,
        run_job_replica_timeout: int | None,
    ):
        return super().__new__(
            cls,
            env_vars=check.opt_sequence_param(env_vars, "env_vars", of_type=str),
            run_resources=check.opt_mapping_param(run_resources, "run_resources", key_type=str),
            server_resources=check.opt_mapping_param(
                server_resources, "server_resources", key_type=str
            ),
            identity_id=check.opt_str_param(identity_id, "identity_id"),
            run_job_replica_timeout=check.opt_int_param(
                run_job_replica_timeout, "run_job_replica_timeout"
            ),
        )

    @classmethod
    def empty(cls) -> "AcaContainerContext":
        """Return a context with every field set to None (the merge identity)."""
        return cls(
            env_vars=None,
            run_resources=None,
            server_resources=None,
            identity_id=None,
            run_job_replica_timeout=None,
        )

    def merge(self, other: "AcaContainerContext") -> "AcaContainerContext":
        return AcaContainerContext(
            env_vars=_dedupe([*other.env_vars, *self.env_vars]),
            run_resources={**self.run_resources, **other.run_resources},
            server_resources={**self.server_resources, **other.server_resources},
            identity_id=other.identity_id or self.identity_id,
            run_job_replica_timeout=(
                other.run_job_replica_timeout
                if other.run_job_replica_timeout is not None
                else self.run_job_replica_timeout
            ),
        )

    def get_environment_dict(self) -> Mapping[str, str]:
        return dict(parse_env_var(e) for e in self.env_vars)

    @staticmethod
    def create_for_run(
        dagster_run: "DagsterRun", run_launcher: "AcaRunLauncher | None"
    ) -> "AcaContainerContext":
        context = AcaContainerContext.empty()
        if run_launcher:
            context = context.merge(
                AcaContainerContext(
                    env_vars=run_launcher.env_vars,
                    run_resources=run_launcher.run_resources,
                    server_resources=None,
                    identity_id=run_launcher.identity_id,
                    run_job_replica_timeout=run_launcher.run_job_replica_timeout,
                )
            )

        run_container_context = (
            dagster_run.job_code_origin.repository_origin.container_context
            if dagster_run.job_code_origin
            else None
        )

        if not run_container_context:
            return context

        return context.merge(AcaContainerContext.create_from_config(run_container_context))

    @staticmethod
    def create_from_config(run_container_context: Mapping[str, Any]) -> "AcaContainerContext":
        processed_shared_container_context = process_shared_container_context_config(
            run_container_context or {}
        )
        shared_container_context = AcaContainerContext(
            env_vars=processed_shared_container_context.get("env_vars", []),
            run_resources=None,
            server_resources=None,
            identity_id=None,
            run_job_replica_timeout=None,
        )

        run_aca_container_context = (
            run_container_context.get("aca", {}) if run_container_context else {}
        )

        if not run_aca_container_context:
            return shared_container_context

        processed_container_context = process_config(
            ACA_CONTAINER_CONTEXT_SCHEMA, run_aca_container_context
        )
        if not processed_container_context.success:
            raise DagsterInvalidConfigError(
                "Errors while parsing Azure Container Apps container context",
                processed_container_context.errors,
                run_aca_container_context,
            )

        value = cast("Mapping[str, Any]", processed_container_context.value)

        return shared_container_context.merge(
            AcaContainerContext(
                env_vars=value.get("env_vars"),
                run_resources=value.get("run_resources"),
                server_resources=value.get("server_resources"),
                identity_id=value.get("identity_id"),
                run_job_replica_timeout=value.get("run_job_replica_timeout"),
            )
        )
