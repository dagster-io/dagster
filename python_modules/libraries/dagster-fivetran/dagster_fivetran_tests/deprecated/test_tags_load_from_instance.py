import responses
from dagster import EnvVar
from dagster._core.instance_for_test import environ
from dagster_fivetran import FivetranResource
from dagster_fivetran.asset_defs import load_assets_from_fivetran_instance

from dagster_fivetran_tests.deprecated.utils import mock_responses


@responses.activate
def test_load_from_instance_with_tags() -> None:
    with environ({"FIVETRAN_API_KEY": "some_key", "FIVETRAN_API_SECRET": "some_secret"}):
        ft_resource = FivetranResource(
            api_key=EnvVar("FIVETRAN_API_KEY"), api_secret=EnvVar("FIVETRAN_API_SECRET")
        )

        mock_responses(ft_resource)

        ft_cacheable_assets = load_assets_from_fivetran_instance(
            ft_resource,
            poll_interval=10,
            poll_timeout=600,
            tags={"dagster/max_retries": "3"},
        )
        ft_assets = ft_cacheable_assets.build_definitions(
            ft_cacheable_assets.compute_cacheable_data()
        )

        assets_def = ft_assets[0]

        for key in assets_def.metadata_by_key.keys():
            assert "dagster/max_retries" in assets_def.tags_by_key[key]