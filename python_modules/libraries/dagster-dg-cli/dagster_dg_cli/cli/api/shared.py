"""Shared utilities for API commands."""

import json
from functools import cache
from typing import Literal

import click
from dagster._record import record
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.api.client import DgApiTestContext


@cache
def get_graphql_error_types() -> set[str]:
    """Returns cached set of all GraphQL error type names from schema.graphql.

    This list is used to identify error responses from the GraphQL API.
    """
    return {
        # Core error types
        "AssetCheckNeedsMigrationError",
        "AssetCheckNeedsUserCodeUpgrade",
        "AssetCheckNeedsAgentUpgradeError",
        "AssetKeyNotFoundError",
        "AssetNotFoundError",
        "AutoMaterializeAssetEvaluationNeedsMigrationError",
        "BackfillNotFoundError",
        "CantRemoveAllAdminsError",
        "CodeLocationLimitError",
        "ConflictingExecutionParamsError",
        "ConfigTypeNotFoundError",
        "CreateOrUpdateMetricsFailed",
        "CustomerInfoNotFoundError",
        "CustomerPaymentMethodRequired",
        "CustomerPaymentRequired",
        "CustomRoleInUseError",
        "CustomRoleNotFoundError",
        "DagsterCloudTokenNotFoundError",
        "DagsterTypeNotFoundError",
        "DeleteFinalDeploymentError",
        "DeploymentLimitError",
        "DeploymentNotFoundError",
        "DuplicateDeploymentError",
        "DuplicateDynamicPartitionError",
        "EnterpriseContractMetadataNotFoundError",
        "EnterpriseUserManagedExpansionNotFoundError",
        "ErrorChainLink",
        "FailedToSetupStripe",
        "FieldNotDefinedConfigError",
        "FieldsNotDefinedConfigError",
        "GitHubError",
        "GraphNotFoundError",
        "InstallationNotFoundError",
        "InstigationStateNotFoundError",
        "InvalidAlertPolicyError",
        "InvalidLocationError",
        "InvalidPipelineRunsFilterError",
        "InvalidSecretInputError",
        "InvalidSubsetError",
        "InvalidTemplateRepoError",
        "MissingFieldConfigError",
        "MissingFieldsConfigError",
        "MissingPermissionsError",
        "ModeNotFoundError",
        "NoModeProvidedError",
        "PartitionKeysNotFoundError",
        "PartitionSetNotFoundError",
        "PartitionSubsetDeserializationError",
        "PipelineNotFoundError",
        "PipelineSnapshotNotFoundError",
        "PresetNotFoundError",
        "PythonError",
        "ReloadNotSupported",
        "RemoveStripePaymentFailedError",
        "ReportingInputError",
        "RepositoryLocationNotFound",
        "RepositoryNotFoundError",
        "ResourceNotFoundError",
        "RestartGitCIError",
        "RunGroupNotFoundError",
        "RunNotFoundError",
        "RunNotificationsExpiredError",
        "RuntimeMismatchConfigError",
        "ScheduleNotFoundError",
        "SchedulerNotDefinedError",
        "SearchQueryError",
        "SearchResultsNotFoundError",
        "SecretAlreadyExistsError",
        "SelectionCantBeDeletedError",
        "SelectionNotResolvableError",
        "SelectorTypeConfigError",
        "SensorNotFoundError",
        "SetupRepoError",
        "ShareFeedbackSubmissionError",
        "SlackIntegrationError",
        "SolidStepStatusUnavailableError",
        "TooManySecretsError",
        "UnauthorizedError",
        "UnknownStripeInvoiceError",
        "UnknownStripePaymentMethodError",
        "UnsupportedOperationError",
        "UpdateCustomerTaxIDError",
        "UpdateStripeSubscriptionFailed",
        "UserLimitError",
        "UserNotFoundError",
    }


def get_config_or_error() -> DagsterPlusCliConfig:
    """Get Dagster Plus config or raise error if not authenticated."""
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg api` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def get_config_for_api_command(ctx: click.Context) -> DagsterPlusCliConfig:
    """Get config for API commands, supporting both test and normal contexts."""
    # Check if we're in a test context
    if ctx.obj and isinstance(ctx.obj, DgApiTestContext):
        # Return a mock config for testing
        return DagsterPlusCliConfig(
            organization=ctx.obj.organization,
            default_deployment=ctx.obj.deployment,
            user_token="test-token",  # Mock token for testing
        )

    # Normal operation - use existing authentication logic
    return get_config_or_error()


@record
class DgApiErrorMapping:
    """Maps GraphQL error types to structured REST-like error metadata.

    While GraphQL typically returns errors as part of the response body with 200 OK status,
    we're enhancing the error information to include REST-style conventions for better
    programmatic handling by CLI tools and scripts.

    This mapping bridges GraphQL's type-based errors to REST API conventions by adding:
    - HTTP status codes for categorizing error severity/type
    - Machine-readable error codes for programmatic handling

    Attributes:
        code: Machine-readable error code following REST API conventions for programmatic error handling
        status_code: HTTP status code that would be returned by an equivalent REST API
    """

    code: Literal[
        # Authentication/Authorization
        "UNAUTHORIZED",
        # Not Found
        "ASSET_NOT_FOUND",
        "PIPELINE_NOT_FOUND",
        "RUN_NOT_FOUND",
        "SCHEDULE_NOT_FOUND",
        "REPOSITORY_NOT_FOUND",
        "CONFIG_TYPE_NOT_FOUND",
        # Client Errors
        "INVALID_SUBSET",
        "INVALID_PARTITION_SUBSET",
        # Server Errors
        "PYTHON_ERROR",
        "SCHEDULER_NOT_DEFINED",
        # Migration/Upgrade
        "MIGRATION_REQUIRED",
        "USER_CODE_UPGRADE_REQUIRED",
        "AGENT_UPGRADE_REQUIRED",
        # Default/Fallback
        "INTERNAL_ERROR",
    ]
    status_code: Literal[400, 401, 403, 404, 422, 500]


def get_error_type_from_status_code(status_code: int) -> str:
    """Returns the error type category for a given HTTP status code."""
    mapping = {
        400: "client_error",
        401: "authentication_error",
        403: "authorization_error",
        404: "not_found_error",
        422: "migration_error",
        500: "server_error",
    }
    return mapping.get(status_code, "server_error")


class DgApiError(click.ClickException):
    """Single exception type for all API errors with structured metadata."""

    def __init__(self, message: str, code: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.error_type = get_error_type_from_status_code(status_code)


@cache
def get_graphql_error_mappings() -> dict[str, DgApiErrorMapping]:
    """Returns cached mapping from GraphQL __typename to error metadata."""
    return {
        # Authentication/Authorization
        "UnauthorizedError": DgApiErrorMapping(
            code="UNAUTHORIZED",
            status_code=401,
        ),
        # Not Found Errors
        "AssetNotFoundError": DgApiErrorMapping(
            code="ASSET_NOT_FOUND",
            status_code=404,
        ),
        "PipelineNotFoundError": DgApiErrorMapping(
            code="PIPELINE_NOT_FOUND",
            status_code=404,
        ),
        "RunNotFoundError": DgApiErrorMapping(
            code="RUN_NOT_FOUND",
            status_code=404,
        ),
        "ScheduleNotFoundError": DgApiErrorMapping(
            code="SCHEDULE_NOT_FOUND",
            status_code=404,
        ),
        "RepositoryNotFoundError": DgApiErrorMapping(
            code="REPOSITORY_NOT_FOUND",
            status_code=404,
        ),
        "ConfigTypeNotFoundError": DgApiErrorMapping(
            code="CONFIG_TYPE_NOT_FOUND",
            status_code=404,
        ),
        # Validation/Client Errors
        "InvalidSubsetError": DgApiErrorMapping(
            code="INVALID_SUBSET",
            status_code=400,
        ),
        "PartitionSubsetDeserializationError": DgApiErrorMapping(
            code="INVALID_PARTITION_SUBSET",
            status_code=400,
        ),
        # Server/System Errors
        "PythonError": DgApiErrorMapping(
            code="PYTHON_ERROR",
            status_code=500,
        ),
        "SchedulerNotDefinedError": DgApiErrorMapping(
            code="SCHEDULER_NOT_DEFINED",
            status_code=500,
        ),
        # Migration/Upgrade Errors
        "AssetCheckNeedsMigrationError": DgApiErrorMapping(
            code="MIGRATION_REQUIRED",
            status_code=422,
        ),
        "AssetCheckNeedsUserCodeUpgrade": DgApiErrorMapping(
            code="USER_CODE_UPGRADE_REQUIRED",
            status_code=422,
        ),
        "AssetCheckNeedsAgentUpgradeError": DgApiErrorMapping(
            code="AGENT_UPGRADE_REQUIRED",
            status_code=422,
        ),
    }


def get_default_error_mapping() -> DgApiErrorMapping:
    """Returns default error mapping for unmapped errors."""
    return DgApiErrorMapping(
        code="INTERNAL_ERROR",
        status_code=500,
    )


def get_or_create_dg_api_error(graphql_error) -> DgApiError:
    """Convert a GraphQL error to a DgApiError instance.

    Args:
        graphql_error: GraphQL error object with message and optional extensions

    Returns:
        DgApiError instance with appropriate code and status
    """
    # Extract error type from GraphQL error extensions
    error_type = None
    if hasattr(graphql_error, "extensions") and graphql_error.extensions:
        error_type = graphql_error.extensions.get("errorType")

    # Get mapping or use default
    mappings = get_graphql_error_mappings()
    if error_type and error_type in mappings:
        mapping = mappings[error_type]
    else:
        mapping = get_default_error_mapping()

    # Create DgApiError with mapped values
    return DgApiError(
        message=str(graphql_error.message), code=mapping.code, status_code=mapping.status_code
    )


def format_error_for_output(exception: Exception, output_json: bool) -> tuple[str, int]:
    """Format an exception for CLI output and return output string and exit code.

    Args:
        exception: The exception to format
        output_json: Whether to format as JSON

    Returns:
        Tuple of (formatted output string, exit code)
    """
    if isinstance(exception, DgApiError):
        if output_json:
            error_dict = {
                "error": str(exception),
                "code": exception.code,
                "statusCode": exception.status_code,
                "type": exception.error_type,
            }
            return json.dumps(error_dict), exception.status_code // 100
        else:
            return f"Error querying Dagster Plus API: {exception}", exception.status_code // 100

    # Fallback for unexpected exceptions
    if output_json:
        error_dict = {
            "error": str(exception),
            "code": "INTERNAL_ERROR",
            "statusCode": 500,
            "type": "server_error",
        }
        return json.dumps(error_dict), 5
    else:
        return f"Error querying Dagster Plus API: {exception}", 1
