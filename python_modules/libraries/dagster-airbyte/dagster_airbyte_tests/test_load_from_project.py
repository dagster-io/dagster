import pytest
import responses
from dagster import AssetKey, build_init_resource_context, materialize, with_resources
from dagster._utils import file_relative_path
from dagster_airbyte import AirbyteResource, airbyte_resource, load_assets_from_airbyte_project
from dagster_airbyte.asset_defs import AirbyteConnectionMetadata

from dagster_airbyte_tests.utils import get_project_connection_json, get_project_job_json


@pytest.fixture(name="airbyte_instance", params=[True, False], scope="module")
def airbyte_instance_fixture(request) -> AirbyteResource:
    if request.param:
        return AirbyteResource(host="some_host", port="8000", poll_interval=0)
    else:
        return airbyte_resource(
            build_init_resource_context({"host": "some_host", "port": "8000", "poll_interval": 0})
        )


@responses.activate
@pytest.mark.parametrize("use_normalization_tables", [True, False])
@pytest.mark.parametrize(
    "connection_to_group_fn, connection_meta_to_group_fn",
    [(None, lambda meta: f"{meta.name[0]}_group"), (None, None), (lambda x: f"{x[0]}_group", None)],
)
@pytest.mark.parametrize("filter_connection", [None, "filter_fn", "dirs"])
@pytest.mark.parametrize(
    "connection_to_asset_key_fn", [None, lambda conn, name: AssetKey([f"{conn.name[0]}_{name}"])]
)
def test_load_from_project(
    use_normalization_tables,
    connection_to_group_fn,
    connection_meta_to_group_fn,
    filter_connection,
    connection_to_asset_key_fn,
    airbyte_instance,
):
    if connection_to_group_fn:
        ab_cacheable_assets = load_assets_from_airbyte_project(
            file_relative_path(__file__, "./test_airbyte_project"),
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
            connection_meta_to_group_fn=connection_meta_to_group_fn,
            connection_filter=(lambda _: False) if filter_connection == "filter_fn" else None,
            connection_directories=(
                ["github_snowflake_ben"] if filter_connection == "dirs" else None
            ),
            connection_to_asset_key_fn=connection_to_asset_key_fn,
        )
    else:
        ab_cacheable_assets = load_assets_from_airbyte_project(
            file_relative_path(__file__, "./test_airbyte_project"),
            create_assets_for_normalization_tables=use_normalization_tables,
            connection_meta_to_group_fn=connection_meta_to_group_fn,
            connection_filter=(lambda _: False) if filter_connection == "filter_fn" else None,
            connection_directories=(
                ["github_snowflake_ben"] if filter_connection == "dirs" else None
            ),
            connection_to_asset_key_fn=connection_to_asset_key_fn,
        )
    ab_assets = ab_cacheable_assets.build_definitions(ab_cacheable_assets.compute_cacheable_data())

    if filter_connection == "filter_fn":
        assert len(ab_assets) == 0
        return

    tables = {
        "dagster_releases",
        "dagster_tags",
        "dagster_teams",
        "dagster_array_test",
        "dagster_unknown_test",
    } | (
        {
            "dagster_releases_assets",
            "dagster_releases_author",
            "dagster_tags_commit",
            "dagster_releases_foo",
            "dagster_array_test_author",
        }
        if use_normalization_tables
        else set()
    )

    if connection_to_asset_key_fn:
        tables = {
            connection_to_asset_key_fn(
                AirbyteConnectionMetadata(
                    "Github <> snowflake-ben", "", use_normalization_tables, []
                ),
                t,
            ).path[0]
            for t in tables
        }

    assert ab_assets[0].keys == {AssetKey(t) for t in tables}
    assert all(
        [
            ab_assets[0].group_names_by_key.get(AssetKey(t))
            == (
                connection_meta_to_group_fn(
                    AirbyteConnectionMetadata(
                        "GitHub <> snowflake-ben", "", use_normalization_tables, []
                    )
                )
                if connection_meta_to_group_fn
                else (
                    connection_to_group_fn("GitHub <> snowflake-ben")
                    if connection_to_group_fn
                    else "github_snowflake_ben"
                )
            )
            for t in tables
        ]
    )
    assert len(ab_assets[0].op.output_defs) == len(tables)

    responses.add(
        method=responses.POST,
        url=airbyte_instance.api_base_url + "/connections/get",
        json=get_project_connection_json(),
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=airbyte_instance.api_base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=airbyte_instance.api_base_url + "/jobs/get",
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
                        "poll_interval": 0,
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
