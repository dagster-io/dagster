from collections.abc import Mapping


class DagsterPlusGraphqlError(Exception):
    """Base for failures surfaced through the Dagster Plus GraphQL API."""


class DagsterPlusServerError(DagsterPlusGraphqlError):
    """Dagster Plus could not serve the request. Nothing the caller can do about it."""


class DagsterPlusClientError(DagsterPlusGraphqlError):
    """The request was rejected for a reason the caller can correct."""


class DagsterPlusUnauthorizedError(DagsterPlusClientError):
    """The caller lacks permission for the request."""


class UnconfirmedProdDeletionError(Exception):
    pass


class S3Error(Exception):
    pass


_TYPENAME_ERRORS: Mapping[str, type[DagsterPlusGraphqlError]] = {
    "AssetCheckNeedsAgentUpgradeError": DagsterPlusClientError,
    "AssetCheckNeedsMigrationError": DagsterPlusClientError,
    "AssetCheckNeedsUserCodeUpgrade": DagsterPlusClientError,
    "AssetNotFoundError": DagsterPlusClientError,
    "AutoMaterializeAssetEvaluationNeedsMigrationError": DagsterPlusClientError,
    "ConflictingExecutionParamsError": DagsterPlusClientError,
    "DeleteFinalDeploymentError": DagsterPlusClientError,
    "DeploymentNotFoundError": DagsterPlusClientError,
    "DuplicateDeploymentError": DagsterPlusClientError,
    "InvalidAlertPolicyError": DagsterPlusClientError,
    "InvalidLocationError": DagsterPlusClientError,
    "InvalidOutputError": DagsterPlusClientError,
    "InvalidPipelineRunsFilterError": DagsterPlusClientError,
    "InvalidStepError": DagsterPlusClientError,
    "InvalidSubsetError": DagsterPlusClientError,
    "NoModeProvidedError": DagsterPlusClientError,
    "PipelineNotFoundError": DagsterPlusClientError,
    "PresetNotFoundError": DagsterPlusClientError,
    "PythonError": DagsterPlusServerError,
    "RepositoryNotFoundError": DagsterPlusClientError,
    "ReportingInputError": DagsterPlusClientError,
    "RunConfigValidationInvalid": DagsterPlusClientError,
    "RunConflict": DagsterPlusClientError,
    "RunNotFoundError": DagsterPlusClientError,
    "RunNotificationsExpiredError": DagsterPlusClientError,
    "ScheduleNotFoundError": DagsterPlusClientError,
    "SensorNotFoundError": DagsterPlusClientError,
    "TerminateRunFailure": DagsterPlusClientError,
    "UnauthorizedError": DagsterPlusUnauthorizedError,
}


def error_for_typename(typename: str) -> type[DagsterPlusGraphqlError]:
    """Exception class for a GraphQL error typename.

    Unrecognized typenames are treated as server faults so that a union member we do not
    handle yet stays visible rather than being reported as the caller's mistake.
    """
    return _TYPENAME_ERRORS.get(typename, DagsterPlusServerError)
