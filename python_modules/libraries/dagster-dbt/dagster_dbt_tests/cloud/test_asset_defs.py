import json

import pytest
import responses
from dagster_dbt import (
    DagsterDbtCloudJobInvariantViolationError,
    dbt_cloud_resource,
    load_assets_from_dbt_cloud_job,
)

from dagster import (
    AssetKey,
    AssetSelection,
    DailyPartitionsDefinition,
    MetadataValue,
    build_init_resource_context,
    define_asset_job,
    file_relative_path,
)

from ..utils import assert_assets_match_project

DBT_CLOUD_API_TOKEN = "abc"
DBT_CLOUD_ACCOUNT_ID = 1
DBT_CLOUD_PROJECT_ID = 12
DBT_CLOUD_JOB_ID = 123
DBT_CLOUD_RUN_ID = 1234

with open(file_relative_path(__file__, "../sample_manifest.json"), "r", encoding="utf8") as f:
    MANIFEST_JSON = json.load(f)

with open(file_relative_path(__file__, "../sample_run_results.json"), "r", encoding="utf8") as f:
    RUN_RESULTS_JSON = json.load(f)


@pytest.fixture(name="dbt_cloud")
def dbt_cloud_fixture():
    yield dbt_cloud_resource.configured(
        {
            "auth_token": DBT_CLOUD_API_TOKEN,
            "account_id": DBT_CLOUD_ACCOUNT_ID,
        }
    )


@pytest.fixture(name="dbt_cloud_service")
def dbt_cloud_service_fixture():
    yield dbt_cloud_resource(
        build_init_resource_context(
            config={
                "auth_token": DBT_CLOUD_API_TOKEN,
                "account_id": DBT_CLOUD_ACCOUNT_ID,
            }
        )
    )


def _add_dbt_cloud_job_responses(dbt_cloud_api_base_url: str, dbt_command: str):
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/",
        json={
            "data": {
                "project_id": DBT_CLOUD_PROJECT_ID,
                "generate_docs": True,
                "execute_steps": [dbt_command],
            }
        },
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/",
        json={"data": {}},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/runs/",
        json={"data": [{"id": DBT_CLOUD_RUN_ID}]},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/runs/{DBT_CLOUD_RUN_ID}/artifacts/manifest.json",
        json=MANIFEST_JSON,
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/runs/{DBT_CLOUD_RUN_ID}/artifacts/run_results.json",
        json=RUN_RESULTS_JSON,
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/run/",
        json={"data": {"id": DBT_CLOUD_RUN_ID, "href": "/"}},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_api_base_url}{DBT_CLOUD_ACCOUNT_ID}/runs/{DBT_CLOUD_RUN_ID}/",
        json={"data": {"status_humanized": "Success", "job": {}, "id": DBT_CLOUD_RUN_ID}},
        status=200,
    )


@responses.activate
@pytest.mark.parametrize("dbt_command", ["dbt run", "dbt build"])
@pytest.mark.parametrize(
    ["dbt_command_options", "expected_dbt_command_options"],
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
    mocker,
    dbt_command,
    dbt_command_options,
    expected_dbt_command_options,
    dbt_cloud,
    dbt_cloud_service,
):
    _add_dbt_cloud_job_responses(
        dbt_cloud_api_base_url=dbt_cloud_service.api_base_url,
        dbt_command=f"{dbt_command} {dbt_command_options}",
    )

    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud, job_id=DBT_CLOUD_JOB_ID
    )

    mock_run_job_and_poll = mocker.patch(
        "dagster_dbt.cloud.resources.DbtCloudResourceV2.run_job_and_poll",
        wraps=dbt_cloud_cacheable_assets._dbt_cloud.run_job_and_poll,  # pylint: disable=protected-access
    )

    dbt_assets_definition_cacheable_data = dbt_cloud_cacheable_assets.compute_cacheable_data()
    dbt_cloud_assets = dbt_cloud_cacheable_assets.build_definitions(
        dbt_assets_definition_cacheable_data
    )

    mock_run_job_and_poll.assert_called_once_with(
        job_id=DBT_CLOUD_JOB_ID,
        cause="Generating software-defined assets for Dagster.",
        steps_override=[f"dbt compile {expected_dbt_command_options}"],
    )

    assert_assets_match_project(dbt_cloud_assets, has_non_argument_deps=True)

    # Assert that the outputs have the correct metadata
    for output in dbt_cloud_assets[0].op.output_dict.values():
        assert output.metadata.keys() == {"dbt Cloud Job", "dbt Cloud Documentation"}
        assert output.metadata["dbt Cloud Job"] == MetadataValue.url(
            dbt_cloud_service.build_url_for_job(
                project_id=DBT_CLOUD_PROJECT_ID, job_id=DBT_CLOUD_JOB_ID
            )
        )

    materialize_cereal_assets = define_asset_job(
        name="materialize_cereal_assets",
        selection=AssetSelection.assets(*dbt_cloud_assets),
    ).resolve(assets=dbt_cloud_assets, source_assets=[])

    assert materialize_cereal_assets.execute_in_process().success


@responses.activate
def test_invalid_dbt_cloud_job(dbt_cloud, dbt_cloud_service):
    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud, job_id=DBT_CLOUD_JOB_ID
    )

    responses.add(
        method=responses.GET,
        url=f"{dbt_cloud_service.api_base_url}{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/",
        json={
            "data": {
                "project_id": DBT_CLOUD_PROJECT_ID,
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
        url=f"{dbt_cloud_service.api_base_url}{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/",
        json={
            "data": {
                "project_id": DBT_CLOUD_PROJECT_ID,
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
        url=f"{dbt_cloud_service.api_base_url}{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/",
        json={
            "data": {
                "project_id": DBT_CLOUD_PROJECT_ID,
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


@responses.activate
def test_custom_groups(dbt_cloud, dbt_cloud_service):
    _add_dbt_cloud_job_responses(
        dbt_cloud_api_base_url=dbt_cloud_service.api_base_url,
        dbt_command="dbt build",
    )

    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud,
        job_id=DBT_CLOUD_JOB_ID,
        node_info_to_group_fn=lambda node_info: node_info["tags"][0],
    )
    dbt_assets_definition_cacheable_data = dbt_cloud_cacheable_assets.compute_cacheable_data()
    dbt_cloud_assets = dbt_cloud_cacheable_assets.build_definitions(
        dbt_assets_definition_cacheable_data
    )

    assert dbt_cloud_assets[0].group_names_by_key == {
        AssetKey(["cold_schema", "sort_cold_cereals_by_calories"]): "foo",
        AssetKey(["sort_by_calories"]): "foo",
        AssetKey(["sort_hot_cereals_by_calories"]): "bar",
        AssetKey(["subdir_schema", "least_caloric"]): "bar",
    }


@responses.activate
def test_node_info_to_asset_key(dbt_cloud, dbt_cloud_service):
    _add_dbt_cloud_job_responses(
        dbt_cloud_api_base_url=dbt_cloud_service.api_base_url,
        dbt_command="dbt build",
    )

    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud,
        job_id=DBT_CLOUD_JOB_ID,
        node_info_to_asset_key=lambda node_info: AssetKey(["foo", node_info["name"]]),
    )
    dbt_assets_definition_cacheable_data = dbt_cloud_cacheable_assets.compute_cacheable_data()
    dbt_cloud_assets = dbt_cloud_cacheable_assets.build_definitions(
        dbt_assets_definition_cacheable_data
    )

    assert dbt_cloud_assets[0].group_names_by_key.keys() == {
        AssetKey(["foo", "sort_cold_cereals_by_calories"]),
        AssetKey(["foo", "sort_by_calories"]),
        AssetKey(["foo", "sort_hot_cereals_by_calories"]),
        AssetKey(["foo", "least_caloric"]),
    }


@responses.activate
def test_partitions(mocker, testrun_uid, dbt_cloud, dbt_cloud_service):
    _add_dbt_cloud_job_responses(
        dbt_cloud_api_base_url=dbt_cloud_service.api_base_url,
        dbt_command="dbt build",
    )

    partition_def = DailyPartitionsDefinition(start_date="2022-01-01")
    dbt_cloud_cacheable_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud,
        job_id=DBT_CLOUD_JOB_ID,
        # HACK: we should refactor to materialize_to_memory, and fix the bug regarding io managers.
        node_info_to_asset_key=lambda node_info: AssetKey(
            ["foo", f"{node_info['name']}-{testrun_uid}"]
        ),
        partitions_def=partition_def,
        partition_key_to_vars_fn=lambda partition_key: {"run_date": partition_key},
    )

    mock_run_job_and_poll = mocker.patch(
        "dagster_dbt.cloud.resources.DbtCloudResourceV2.run_job_and_poll",
        wraps=dbt_cloud_cacheable_assets._dbt_cloud.run_job_and_poll,  # pylint: disable=protected-access
    )

    dbt_assets_definition_cacheable_data = dbt_cloud_cacheable_assets.compute_cacheable_data()
    dbt_cloud_assets = dbt_cloud_cacheable_assets.build_definitions(
        dbt_assets_definition_cacheable_data
    )

    mock_run_job_and_poll.assert_called_once_with(
        job_id=DBT_CLOUD_JOB_ID,
        cause="Generating software-defined assets for Dagster.",
        steps_override=[
            f"dbt compile --vars '{json.dumps({'run_date': partition_def.get_last_partition_key()})}'"
        ],
    )

    mock_run_job_and_poll.reset_mock()

    materialize_cereal_assets = define_asset_job(
        name="materialize_partitioned_cereal_assets",
        selection=AssetSelection.assets(*dbt_cloud_assets),
    ).resolve(assets=dbt_cloud_assets, source_assets=[])

    assert materialize_cereal_assets.execute_in_process(partition_key="2022-02-01").success

    mock_run_job_and_poll.assert_called_once_with(
        job_id=DBT_CLOUD_JOB_ID,
        steps_override=[f"dbt build --vars '{json.dumps({'run_date': '2022-02-01'})}'"],
    )
