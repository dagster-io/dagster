"""Registry of all API classes for REST compliance testing."""

from dagster_dg_cli.dagster_plus_api.api.deployments import DgApiDeploymentApi


def get_all_api_classes():
    """Get all API classes to test."""
    # For now just DgApiDeploymentApi, but this can be expanded
    return [DgApiDeploymentApi]
