import platform
from typing import Optional

from ...version import __version__
from .auth import (
    API_TOKEN_HEADER,
    DAGSTER_CLOUD_SCOPE_HEADER,
    DEPLOYMENT_NAME_HEADER,
    DagsterCloudInstanceScope,
)
from .versioning.constants import DAGSTER_CLOUD_VERSION_HEADER, PYTHON_VERSION_HEADER


def get_dagster_cloud_api_headers(
    agent_token: str,
    scope: DagsterCloudInstanceScope,
    deployment_name: Optional[str] = None,
    additional_headers: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    return {
        **{
            API_TOKEN_HEADER: agent_token,
            PYTHON_VERSION_HEADER: platform.python_version(),
            DAGSTER_CLOUD_VERSION_HEADER: __version__,
            DAGSTER_CLOUD_SCOPE_HEADER: scope.value,
        },
        **({DEPLOYMENT_NAME_HEADER: deployment_name} if deployment_name else {}),
        **(additional_headers if additional_headers else {}),
    }
