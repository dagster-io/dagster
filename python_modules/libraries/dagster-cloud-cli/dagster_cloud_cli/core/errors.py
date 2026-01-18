from requests import HTTPError


class DagsterCloudAgentServerError(Exception):
    """Raise this when there's an error in the GraphQL layer."""


DEFAULT_MAINTENANCE_TIMEOUT = 3600 * 4 * 4
DEFAULT_MAINTENANCE_RETRY_INTERVAL = 30


class DagsterCloudMaintenanceException(Exception):
    def __init__(self, message, timeout, retry_interval):
        self.timeout = timeout or DEFAULT_MAINTENANCE_TIMEOUT
        self.retry_interval = retry_interval or DEFAULT_MAINTENANCE_RETRY_INTERVAL
        super().__init__(message)


class DagsterCloudHTTPError(Exception):
    """Clearer error message for exceptions hitting Dagster Cloud servers."""

    def __init__(self, http_error: HTTPError):
        self.response = http_error.response
        error_content = http_error.response.content.decode("utf-8", errors="ignore")
        super().__init__(http_error.__str__() + ": " + str(error_content))


def raise_http_error(response):
    try:
        response.raise_for_status()
    except HTTPError as e:
        raise DagsterCloudHTTPError(e) from e
