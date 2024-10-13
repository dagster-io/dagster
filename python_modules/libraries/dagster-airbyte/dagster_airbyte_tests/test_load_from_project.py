import pytest
import responses
import yaml
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

    with open(
        file_relative_path(
            __file__, "./test_airbyte_project/destinations/snowflake_ben/configuration.yaml"
        ),
        encoding="utf-8",
    ) as f:
        destination_data = yaml.safe_load(f.read())

    if connection_to_asset_key_fn:
        tables = {
            connection_to_asset_key_fn(
                AirbyteConnectionMetadata(
                    "Github <> snowflake-ben", "", use_normalization_tables, [], destination_data
                ),
                t,
            ).path[0]
            for t in tables
        }

    # Check metadata is added correctly to asset def
    assets_def = ab_assets[0]

    relation_identifiers = {
        "AIRBYTE.BEN_DEMO.releases",
        "AIRBYTE.BEN_DEMO.tags",
        "AIRBYTE.BEN_DEMO.teams",
        "AIRBYTE.BEN_DEMO.array_test",
        "AIRBYTE.BEN_DEMO.unknown_test",
    } | (
        {
            "AIRBYTE.BEN_DEMO.releases.assets",
            "AIRBYTE.BEN_DEMO.releases.author",
            "AIRBYTE.BEN_DEMO.tags.commit",
            "AIRBYTE.BEN_DEMO.releases.foo",
            "AIRBYTE.BEN_DEMO.array_test.author",
        }
        if use_normalization_tables
        else set()
    )

    for key, metadata in assets_def.metadata_by_key.items():
        # Extract the table name from the asset key
        table_name = (
            key.path[-1]
            .replace("dagster_", "")
            .replace("G_", "")
            .replace("_test", "")
            .split("_")[-1]
        )
        assert metadata["dagster/relation_identifier"] in relation_identifiers
        assert table_name in metadata["dagster/relation_identifier"]

    assert assets_def.keys == {AssetKey(t) for t in tables}
    assert all(
        [
            assets_def.group_names_by_key.get(AssetKey(t))
            == (
                connection_meta_to_group_fn(
                    AirbyteConnectionMetadata(
                        "GitHub <> snowflake-ben",
                        "",
                        use_normalization_tables,
                        [],
                        destination_data,
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
    assert len(assets_def.op.output_defs) == len(tables)

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
        for event in res.events_for_node("airbyte_sync_87b7fe85_a22c_420e_8d74_b30e7ede77df")
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == len(tables)
    assert {m.asset_key for m in materializations} == {AssetKey(t) for t in tables}
