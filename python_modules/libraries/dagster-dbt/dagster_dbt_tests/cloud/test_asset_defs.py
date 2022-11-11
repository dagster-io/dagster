import json

import responses
from dagster_dbt import dbt_cloud_resource, load_assets_from_dbt_cloud_job

from dagster import build_init_resource_context, file_relative_path

from ..utils import assert_assets_match_project


@responses.activate
def test_load_assets_from_dbt_cloud_job():
    account_id = 123
    run_id = 1234

    manifest_path = file_relative_path(__file__, "../sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    run_results_path = file_relative_path(__file__, "../sample_run_results.json")
    with open(run_results_path, "r", encoding="utf8") as f:
        run_results_json = json.load(f)

    api_base_url = dbt_cloud_resource(
        build_init_resource_context(
            config={
                "auth_token": "abc",
                "account_id": account_id,
            }
        )
    ).api_base_url

    dbt_cloud = dbt_cloud_resource.configured(
        {
            "auth_token": "abc",
            "account_id": account_id,
        }
    )

    responses.add(
        method=responses.GET,
        url=f"{api_base_url}{account_id}/runs/",
        json={"data": [{"id": run_id}]},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{api_base_url}{account_id}/runs/{run_id}/artifacts/manifest.json",
        json=manifest_json,
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{api_base_url}{account_id}/runs/{run_id}/artifacts/run_results.json",
        json=run_results_json,
        status=200,
    )

    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(dbt_cloud=dbt_cloud, job_id=1)
    dbt_cloud_assets = dbt_cloud_cacheable_assets.build_definitions(
        dbt_cloud_cacheable_assets.compute_cacheable_data()
    )

    assert_assets_match_project(dbt_cloud_assets, has_non_argument_deps=True)
