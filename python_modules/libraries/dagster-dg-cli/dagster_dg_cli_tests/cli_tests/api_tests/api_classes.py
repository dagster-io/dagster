"""Registry of all API classes for REST compliance testing."""

from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi
from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi


def get_all_api_classes():
    """Get all API classes to test."""
    return [
        DgApiDeploymentApi,
        DgApiAssetApi,
    ]
