import pytest
import responses
from dagster_airbyte import airbyte_resource, load_assets_from_airbyte_project

from dagster import AssetKey, build_init_resource_context, materialize, with_resources
from dagster._utils import file_relative_path

from .utils import get_project_connection_json, get_project_job_json


@responses.activate
@pytest.mark.parametrize("use_normalization_tables", [True, False])
@pytest.mark.parametrize("connection_to_group_fn", [None, lambda x: f"{x[0]}_group"])
@pytest.mark.parametrize("filter_connection", [True, False])
def test_load_from_project(use_normalization_tables, connection_to_group_fn, filter_connection):

    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )

    if connection_to_group_fn:
        ab_assets = load_assets_from_airbyte_project(
            file_relative_path(__file__, "./test_airbyte_project"),
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
            connection_filter=(lambda _: False) if filter_connection else None,
        )
    else:
        ab_assets = load_assets_from_airbyte_project(
            file_relative_path(__file__, "./test_airbyte_project"),
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_filter=(lambda _: False) if filter_connection else None,
        )

    if filter_connection:
        assert len(ab_assets) == 0
        return

    tables = {"dagster_releases", "dagster_tags", "dagster_teams"} | (
        {"dagster_releases_assets", "dagster_releases_author", "dagster_tags_commit"}
        if use_normalization_tables
        else set()
    )
    assert ab_assets[0].keys == {AssetKey(t) for t in tables}
    assert all(
        [
            ab_assets[0].group_names_by_key.get(AssetKey(t))
            == (
                connection_to_group_fn("github_snowflake_ben")
                if connection_to_group_fn
                else "github_snowflake_ben"
            )
            for t in tables
        ]
    )
    assert len(ab_assets[0].op.output_defs) == len(tables)

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/get",
        json=get_project_connection_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs/get",
        json=get_project_job_json(),
        status=200,
    )

    res = materialize(
        with_resources(
            ab_assets,
            resource_defs={
                "airbyte": airbyte_resource.configured(
                    {
                        "host": "some_host",
                        "port": "8000",
                    }
                )
            },
        )
    )

    materializations = [
        event.event_specific_data.materialization
        for event in res.events_for_node("airbyte_sync_87b7f")
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == len(tables)
    assert {m.asset_key for m in materializations} == {AssetKey(t) for t in tables}
