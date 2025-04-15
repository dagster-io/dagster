from contextlib import contextmanager
from typing import Any, Optional

from dagster_shared import check

from dagster_cloud_cli import gql
from dagster_cloud_cli.config_utils import get_user_token


@contextmanager
def client_from_env(url: str, deployment: Optional[str] = None):
    if deployment:
        url = url + "/" + deployment
    with gql.graphql_client_from_url(
        url, check.not_none(get_user_token()), deployment_name=deployment
    ) as client:
        yield client


def get_registry_info(url: str) -> dict[str, Any]:
    with client_from_env(url) as client:
        return gql.get_ecr_info(client)
