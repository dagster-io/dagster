from enum import Enum
from typing import Mapping, NamedTuple, Optional, cast

from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.events import Output
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import MetadataEntry, MetadataValue
from dagster._core.definitions.output import Out
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
class VerificationStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@whitelist_for_serdes
class VerificationResult(NamedTuple):
    status: VerificationStatus
    message: Optional[str]

    @classmethod
    def success(cls, message: Optional[str] = None):
        """Create a successful verification result.
        """
        return cls(VerificationStatus.SUCCESS, message)

    @classmethod
    def failure(cls, message: Optional[str] = None):
        """Create a failed verification result.
        """
        return cls(VerificationStatus.FAILURE, message)


class ConfigVerifiable:
    def verify_config(self) -> VerificationResult:
        raise NotImplementedError()


def resource_verification_job_name(resource_key: str) -> str:
    return f"__RESOURCE_VERIFICATION_{resource_key}"


def resource_verification_op_name(resource_key: str) -> str:
    return f"config_check_{resource_key}"


def is_resource_verifiable(resource: ResourceDefinition) -> bool:
    """Returns whether the resource is (or wraps) a ConfigVerifiable resource.
    """
    from dagster._config.structured_config import ResourceWithKeyMapping, is_fully_configured

    if isinstance(resource, ResourceWithKeyMapping):
        return is_resource_verifiable(resource.wrapped_resource)

    if not is_fully_configured(resource):
        return False
    return isinstance(resource, ConfigVerifiable)


def create_resource_verification_job(
    resource_key: str, resource_defs: Mapping[str, ResourceDefinition]
) -> JobDefinition:
    """Creates a job which wraps the config check method for a ConfigVerifiable resource. The output is
    recorded in metadata of the op output.
    """

    @op(
        name=resource_verification_op_name(resource_key),
        required_resource_keys={resource_key},
        out={"result": Out(VerificationResult)},
    )
    def resource_verification_op(context: OpExecutionContext) -> Output[VerificationResult]:
        result = cast(ConfigVerifiable, getattr(context.resources, resource_key)).verify_config()

        return Output(
            result,
            metadata_entries=[
                MetadataEntry("status", value=MetadataValue.text(result.status.name)),
                MetadataEntry(
                    "message",
                    value=MetadataValue.text(result.message)
                    if result.message
                    else MetadataValue.null(),
                ),
            ],
        )

    @job(name=resource_verification_job_name(resource_key), resource_defs=resource_defs)
    def resource_verification_job() -> None:
        resource_verification_op()

    return resource_verification_job
