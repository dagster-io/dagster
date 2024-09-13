import responses
from dagster._core.instance_for_test import instance_for_test


@responses.activate
def test_load_assets_organization_data(sigma_auth_token: str, sigma_sample_data: None) -> None:
    with instance_for_test() as _instance:
        from dagster_sigma_tests.pending_repo import pending_repo_from_cached_asset_metadata

        # first, we resolve the repository to generate our cached metadata
        repository_def = pending_repo_from_cached_asset_metadata.compute_repository_definition()

        # 2 Sigma external assets, one materializable asset
        assert len(repository_def.assets_defs_by_key) == 2 + 1
