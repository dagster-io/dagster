import os
from pathlib import Path
from typing import Optional, Union

import requests

from dagster_cloud_cli.config_utils import (
    URL_ENV_VAR_NAME,
    get_deployment,
    get_organization,
    get_user_token,
)
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from dagster_cloud_cli.core.headers.impl import get_dagster_cloud_api_headers
from dagster_cloud_cli.gql import url_from_config


def _dagster_cloud_http_client():
    # indirection for mocking, could share a session
    return requests


def download_artifact(
    *,
    url: str,
    api_token: str,
    scope: DagsterCloudInstanceScope,
    key: str,
    path: Union[Path, str],
):
    response = _dagster_cloud_http_client().post(
        url=f"{url}/gen_artifact_get",
        headers=get_dagster_cloud_api_headers(
            api_token,
            scope,
        ),
        json={"key": key},
    )
    response.raise_for_status()

    payload = response.json()

    response = requests.get(
        payload["url"],
    )
    response.raise_for_status()
    Path(path).write_bytes(response.content)


def upload_artifact(
    *,
    url: str,
    api_token: str,
    scope: DagsterCloudInstanceScope,
    key: str,
    path: Union[Path, str],
    deployment: Optional[str] = None,
):
    upload_file = Path(path).resolve(strict=True)

    response = _dagster_cloud_http_client().post(
        url=f"{url}/gen_artifact_post",
        headers=get_dagster_cloud_api_headers(
            api_token,
            scope,
        ),
        json={"key": key},
    )
    response.raise_for_status()
    payload = response.json()

    response = requests.post(
        payload["url"],
        data=payload["fields"],
        files={
            "file": upload_file.open(),
        },
    )
    response.raise_for_status()


def _resolve_org(passed_org: Optional[str]) -> str:
    org = passed_org or get_organization()
    if org is None:
        raise Exception(
            "Unable to resolve organization, pass organization or set the "
            "DAGSTER_CLOUD_ORGANIZATION environment variable."
        )
    return org


def _resolve_token(passed_token: Optional[str]) -> str:
    api_token = get_user_token()
    if api_token is None:
        raise Exception(
            "Unable to resolve api_token, pass api_token or set the "
            "DAGSTER_CLOUD_API_TOKEN environment variable"
        )
    return api_token


def _resolve_deploy(passed_deploy: Optional[str]) -> str:
    deploy = passed_deploy or get_deployment()
    if deploy is None:
        raise Exception(
            "Unable to resolve deployment, pass deployment or set the "
            "DAGSTER_CLOUD_DEPLOYMENT environment variable."
        )
    return deploy


def _resolve_url(organization: str, deployment: Optional[str] = None) -> str:
    env_url = os.getenv(URL_ENV_VAR_NAME)
    if env_url:
        return env_url

    return url_from_config(organization, deployment)


def upload_organization_artifact(
    key: str,
    path: Union[str, Path],
    organization: Optional[str] = None,
    api_token: Optional[str] = None,
):
    upload_artifact(
        url=_resolve_url(
            organization=_resolve_org(organization),
        ),
        api_token=_resolve_token(api_token),
        scope=DagsterCloudInstanceScope.ORGANIZATION,
        key=key,
        path=path,
    )


def upload_deployment_artifact(
    key: str,
    path: Union[str, Path],
    organization: Optional[str] = None,
    deployment: Optional[str] = None,
    api_token: Optional[str] = None,
):
    upload_artifact(
        url=_resolve_url(
            organization=_resolve_org(organization),
            deployment=_resolve_deploy(deployment),
        ),
        api_token=_resolve_token(api_token),
        scope=DagsterCloudInstanceScope.DEPLOYMENT,
        key=key,
        path=path,
    )


def download_organization_artifact(
    key: str,
    path: Union[str, Path],
    organization: Optional[str] = None,
    api_token: Optional[str] = None,
):
    download_artifact(
        url=_resolve_url(
            organization=_resolve_org(organization),
        ),
        api_token=_resolve_token(api_token),
        scope=DagsterCloudInstanceScope.ORGANIZATION,
        key=key,
        path=path,
    )


def download_deployment_artifact(
    key: str,
    path: Union[str, Path],
    organization: Optional[str] = None,
    deployment: Optional[str] = None,
    api_token: Optional[str] = None,
):
    deployment = _resolve_deploy(deployment)
    download_artifact(
        url=_resolve_url(
            organization=_resolve_org(organization),
            deployment=deployment,
        ),
        api_token=_resolve_token(api_token),
        scope=DagsterCloudInstanceScope.DEPLOYMENT,
        key=key,
        path=path,
    )
