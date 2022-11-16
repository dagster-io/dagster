import json

import pytest
import responses
from dagster_dbt import (
    DagsterDbtCloudJobInvariantViolationError,
    dbt_cloud_resource,
    load_assets_from_dbt_cloud_job,
)

from dagster import (
    AssetSelection,
    MetadataValue,
    build_init_resource_context,
    define_asset_job,
    file_relative_path,
)

from ..utils import assert_assets_match_project


@responses.activate
@pytest.mark.parametrize("dbt_command", ["dbt run", "dbt build"])
@pytest.mark.parametrize(
    ["dbt_command_filters", "expected_dbt_command_filters"],
    [
        ("-s a:b c:d *x", "--select a:b c:d *x"),
        ("--exclude e:f g:h", "--exclude e:f g:h"),
        ("--selector x:y", "--selector x:y"),
        (
            "-s a:b c:d --exclude e:f g:h --selector x:y",
            "--select a:b c:d --exclude e:f g:h --selector x:y",
        ),
    ],
)
def test_load_assets_from_dbt_cloud_job(
    mocker, dbt_command, dbt_command_filters, expected_dbt_command_filters
):
    account_id = 1
    project_id = 12
    job_id = 123
    run_id = 1234

    manifest_path = file_relative_path(__file__, "../sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    run_results_path = file_relative_path(__file__, "../sample_run_results.json")
    with open(run_results_path, "r", encoding="utf8") as f:
        run_results_json = json.load(f)

    dbt_cloud_service = dbt_cloud_resource(
        build_init_resource_context(
            config={
                "auth_token": "abc",
                "account_id": account_id,
            }
        )
    )

    dbt_cloud = dbt_cloud_resource.configured(
        {
            "auth_token": "abc",
            "account_id": account_id,
        }
    )

    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/jobs/{job_id}/",
        json={
            "data": {
                "project_id": project_id,
                "generate_docs": True,
                "execute_steps": [f"{dbt_command} {dbt_command_filters}"],
            }
        },
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/jobs/{job_id}/",
        json={"data": {}},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/runs/",
        json={"data": [{"id": run_id}]},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/runs/{run_id}/artifacts/manifest.json",
        json=manifest_json,
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/runs/{run_id}/artifacts/run_results.json",
        json=run_results_json,
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/jobs/{job_id}/run/",
        json={"data": {"id": run_id, "href": "/"}},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/runs/{run_id}/",
        json={"data": {"status_humanized": "Success", "job": {}, "id": run_id}},
        status=200,
    )

    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(dbt_cloud=dbt_cloud, job_id=job_id)

    mock_run_job_and_poll = mocker.patch.object(
        dbt_cloud_cacheable_assets._dbt_cloud,  # pylint: disable=protected-access
        "run_job_and_poll",
        wraps=dbt_cloud_cacheable_assets._dbt_cloud.run_job_and_poll,  # pylint: disable=protected-access
    )

    dbt_assets_definition_cacheable_data = dbt_cloud_cacheable_assets.compute_cacheable_data()
    dbt_cloud_assets = dbt_cloud_cacheable_assets.build_definitions(
        dbt_assets_definition_cacheable_data
    )

    mock_run_job_and_poll.assert_called_once_with(
        job_id=job_id,
        cause="Generating software-defined assets for Dagster.",
        steps_override=[f"dbt compile {expected_dbt_command_filters}"],
    )

    assert_assets_match_project(dbt_cloud_assets, has_non_argument_deps=True)

    # Assert that the outputs have the correct metadata
    for output in dbt_cloud_assets[0].op.output_dict.values():
        assert output.metadata.keys() == {"dbt Cloud Job", "dbt Cloud Documentation"}
        assert output.metadata["dbt Cloud Job"] == MetadataValue.url(
            dbt_cloud_service.build_url_for_job(project_id=project_id, job_id=job_id)
        )

    materialize_cereal_assets = define_asset_job(
        name="materialize_cereal_assets",
        selection=AssetSelection.assets(*dbt_cloud_assets),
    ).resolve(assets=dbt_cloud_assets, source_assets=[])

    assert materialize_cereal_assets.execute_in_process().success


@responses.activate
def test_invalid_dbt_cloud_job():
    account_id = 1
    project_id = 12
    job_id = 123

    dbt_cloud_service = dbt_cloud_resource(
        build_init_resource_context(
            config={
                "auth_token": "abc",
                "account_id": account_id,
            }
        )
    )
    dbt_cloud = dbt_cloud_resource.configured(
        {
            "auth_token": "abc",
            "account_id": account_id,
        }
    )

    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(dbt_cloud=dbt_cloud, job_id=job_id)

    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/jobs/{job_id}/",
        json={
            "data": {
                "project_id": project_id,
                "generate_docs": True,
                "execute_steps": [],
                "name": "A dbt Cloud job",
                "id": "1",
            }
        },
        status=200,
    )
    with pytest.raises(DagsterDbtCloudJobInvariantViolationError):
        dbt_cloud_cacheable_assets.compute_cacheable_data()

    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/jobs/{job_id}/",
        json={
            "data": {
                "project_id": project_id,
                "generate_docs": True,
                "execute_steps": ["dbt deps"],
                "name": "A dbt Cloud job",
                "id": "1",
            }
        },
        status=200,
    )
    with pytest.raises(DagsterDbtCloudJobInvariantViolationError):
        dbt_cloud_cacheable_assets.compute_cacheable_data()

    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{account_id}/jobs/{job_id}/",
        json={
            "data": {
                "project_id": project_id,
                "generate_docs": True,
                "execute_steps": ["dbt deps", "dbt build"],
                "name": "A dbt Cloud job",
                "id": "1",
            }
        },
        status=200,
    )
    with pytest.raises(DagsterDbtCloudJobInvariantViolationError):
        dbt_cloud_cacheable_assets.compute_cacheable_data()
