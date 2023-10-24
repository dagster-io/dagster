import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dagster import (
    AssetIn,
    AssetKey,
    AutoMaterializePolicy,
    DailyPartitionsDefinition,
    FreshnessPolicy,
    ResourceDefinition,
    asset,
    materialize_to_memory,
    repository,
)
from dagster._core.definitions import build_assets_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.execution.with_resources import with_resources
from dagster._utils import file_relative_path
from dagster_dbt import (
    DagsterDbtError,
    DagsterDbtTranslator,
    DbtCliClientResource,
    DbtCliResource,
    dbt_cli_resource,
    get_asset_key_for_model,
    group_from_dbt_resource_props_fallback_to_directory,
)
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest, load_assets_from_dbt_project
from dagster_dbt.core.resources import DbtCliClient
from dagster_dbt.core.utils import parse_run_results
from dagster_dbt.errors import DagsterDbtCliFatalRuntimeError, DagsterDbtCliRuntimeError
from dagster_dbt.types import DbtOutput
from dagster_duckdb import build_duckdb_io_manager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler
from pandas import read_csv

from .utils import assert_assets_match_project

manifest_path = Path(__file__).joinpath("..", "sample_manifest.json").resolve()
manifest_json = json.loads(manifest_path.read_bytes())


def test_custom_resource_key_asset_load(
    dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir
):
    dbt_assets = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, dbt_resource_key="my_custom_dbt"
    )
    assert_assets_match_project(dbt_assets)

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "my_custom_dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    ).execute_in_process()

    assert result.success


@pytest.mark.parametrize(
    "prefix",
    [
        None,
        "snowflake",
        ["snowflake", "dbt_schema"],
    ],
)
def test_load_from_manifest_json(prefix):
    run_results_path = file_relative_path(__file__, "sample_run_results.json")
    with open(run_results_path, "r", encoding="utf8") as f:
        run_results_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json=manifest_json, key_prefix=prefix)
    assert_assets_match_project(dbt_assets, prefix=prefix)

    dbt = MagicMock(spec=DbtCliClient)
    dbt.get_run_results_json.return_value = run_results_json
    dbt.run.return_value = DbtOutput(run_results_json)
    dbt.build.return_value = DbtOutput(run_results_json)
    dbt.get_manifest_json.return_value = manifest_json
    dbt._json_log_format = True  # noqa: SLF001
    assets_job = build_assets_job(
        "assets_job",
        dbt_assets,
        resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)},
    )
    assert assets_job.execute_in_process().success


@pytest.mark.parametrize("manifest", [json.loads(manifest_path.read_bytes()), manifest_path])
def test_manifest_argument(manifest):
    my_dbt_assets = load_assets_from_dbt_manifest(manifest)

    assert my_dbt_assets[0].keys == {
        AssetKey.from_user_string(key)
        for key in [
            "sort_by_calories",
            "cold_schema/sort_cold_cereals_by_calories",
            "subdir_schema/least_caloric",
            "sort_hot_cereals_by_calories",
            "orders_snapshot",
            "cereals",
        ]
    }


def test_runtime_metadata_fn(
    dbt_seed,
    dbt_cli_resource_factory,
    test_project_dir,
    dbt_config_dir,
):
    def runtime_metadata_fn(context, node_info):
        return {"op_name": context.op_def.name, "dbt_model": node_info["name"]}

    dbt_assets = load_assets_from_dbt_manifest(
        manifest_json=manifest_json, runtime_metadata_fn=runtime_metadata_fn
    )
    assert_assets_match_project(dbt_assets)

    dbt_resource = dbt_cli_resource_factory(
        project_dir=test_project_dir, profiles_dir=dbt_config_dir
    )
    assets_job = build_assets_job("assets_job", dbt_assets, resource_defs={"dbt": dbt_resource})

    if isinstance(dbt_resource, DbtCliResource):
        with pytest.raises(
            DagsterDbtError,
            match="The runtime_metadata_fn argument on the load_assets_from_dbt_manifest",
        ):
            assets_job.execute_in_process()
    else:
        result = assets_job.execute_in_process()
        assert result.success

        materializations = [
            event.event_specific_data.materialization
            for event in result.events_for_node(dbt_assets[0].op.name)
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 6
        assert materializations[0].metadata["op_name"] == MetadataValue.text(dbt_assets[0].op.name)
        assert materializations[0].metadata["dbt_model"] == MetadataValue.text(
            materializations[0].asset_key.path[-1]
        )


def test_fail_immediately(
    dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir
) -> None:
    from dagster import build_init_resource_context

    dbt_assets = load_assets_from_dbt_project(test_project_dir, dbt_config_dir)
    good_dbt = dbt_cli_resource_factory(
        project_dir=test_project_dir,
        profiles_dir=dbt_config_dir,
    )

    # ensure that there will be a run results json
    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={"dbt": good_dbt},
    ).execute_in_process()

    if isinstance(good_dbt, DbtCliClientResource):
        assert (
            good_dbt.with_replaced_resource_context(build_init_resource_context())
            .get_dbt_client()
            .get_run_results_json()
        )
    elif isinstance(good_dbt, DbtCliResource):
        assert parse_run_results(test_project_dir)
    else:
        assert good_dbt(build_init_resource_context()).get_run_results_json()

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir,
                profiles_dir="BAD PROFILES DIR",
                profile="BAD PROFILE",
            )
        },
    ).execute_in_process(raise_on_error=False)

    assert not result.success
    materializations = [
        event.event_specific_data.materialization  # type: ignore
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 0


@pytest.mark.parametrize(
    "use_build, fail_test, json_log_format",
    [(True, False, True), (True, True, True), (False, False, True), (True, True, False)],
)
def test_basic(
    capsys,
    dbt_seed,
    dbt_cli_resource_factory,
    test_project_dir,
    dbt_config_dir,
    use_build,
    fail_test,
    json_log_format,
):
    dbt_resource = dbt_cli_resource_factory(
        project_dir=test_project_dir,
        profiles_dir=dbt_config_dir,
        json_log_format=json_log_format,
    )
    if not json_log_format and isinstance(dbt_resource, DbtCliResource):
        pytest.skip("DbtCliResource does not support json_log_format")

    # expected to emit json-formatted messages
    with capsys.disabled():
        dbt_assets = load_assets_from_dbt_project(
            test_project_dir,
            dbt_config_dir,
            use_build_command=use_build,
        )

    assert len(dbt_assets[0].group_names_by_key) == len(dbt_assets[0].keys)
    assert set(dbt_assets[0].group_names_by_key.values()) == {"default"}
    assert dbt_assets[0].op.name == "run_dbt_5ad73"
    assert get_asset_key_for_model(dbt_assets, "sort_by_calories") == AssetKey(["sort_by_calories"])

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={"dbt": dbt_resource},
    ).execute_in_process(
        raise_on_error=False,
        run_config={"ops": {dbt_assets[0].op.name: {"config": {"vars": {"fail_test": fail_test}}}}},
    )

    assert result.success == (not fail_test)
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    if fail_test:
        # the test will fail after the first seed/model is completed, so others will not be emitted
        assert len(materializations) == 2
        asset_keys = {mat.asset_key for mat in materializations}
        assert asset_keys == {AssetKey(["cereals"]), AssetKey(["sort_by_calories"])}
    else:
        if use_build:
            # the seed / snapshot will be counted as assets
            assert len(materializations) == 6
        else:
            assert len(materializations) == 4
    observations = [
        event.event_specific_data.asset_observation
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_OBSERVATION"
    ]
    if use_build:
        # when fail_test is set to true, one of the downstream tests will be skipped
        assert len(observations) == (16 if fail_test else 17)
    else:
        assert len(observations) == 0

    captured = capsys.readouterr()

    # make sure we're not logging the raw json to the console
    if not isinstance(dbt_resource, DbtCliResource):
        for output in [captured.out, captured.err]:
            for line in output.split("\n"):
                # we expect a line like --vars {"fail_test": True}
                if "vars" in line:
                    continue
                assert "{" not in line


def test_groups_from_directories(dbt_seed, test_project_dir, dbt_config_dir):
    dbt_assets = load_assets_from_dbt_project(
        test_project_dir,
        dbt_config_dir,
        node_info_to_group_fn=group_from_dbt_resource_props_fallback_to_directory,
    )

    assert dbt_assets[0].group_names_by_key == {
        AssetKey(["cold_schema", "sort_cold_cereals_by_calories"]): "default",
        AssetKey(["sort_by_calories"]): "default",
        AssetKey(["sort_hot_cereals_by_calories"]): "default",
        AssetKey(["subdir_schema", "least_caloric"]): "subdir",
        AssetKey(["cereals"]): "default",
        AssetKey(["orders_snapshot"]): "sort_snapshot",
    }


def test_custom_groups(dbt_seed, test_project_dir, dbt_config_dir):
    def _node_info_to_group(node_info):
        return node_info["tags"][0] if node_info["tags"] else "default"

    dbt_assets = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, node_info_to_group_fn=_node_info_to_group
    )

    assert dbt_assets[0].group_names_by_key == {
        AssetKey(["cold_schema", "sort_cold_cereals_by_calories"]): "foo",
        AssetKey(["sort_by_calories"]): "foo",
        AssetKey(["sort_hot_cereals_by_calories"]): "bar",
        AssetKey(["subdir_schema", "least_caloric"]): "bar",
        AssetKey(["cereals"]): "default",
        AssetKey(["orders_snapshot"]): "default",
    }


def test_custom_freshness_policy():
    dbt_assets = load_assets_from_dbt_manifest(
        manifest_json=manifest_json,
        node_info_to_freshness_policy_fn=lambda node_info: FreshnessPolicy(
            maximum_lag_minutes=len(node_info["name"])
        ),
    )

    assert dbt_assets[0].freshness_policies_by_key == {
        key: FreshnessPolicy(maximum_lag_minutes=len(key.path[-1])) for key in dbt_assets[0].keys
    }


def test_custom_auto_materialize_policy():
    dbt_assets = load_assets_from_dbt_manifest(
        manifest_json=manifest_json,
        node_info_to_auto_materialize_policy_fn=lambda _: AutoMaterializePolicy.lazy(),
    )

    assert dbt_assets[0].auto_materialize_policies_by_key == {
        key: AutoMaterializePolicy.lazy() for key in dbt_assets[0].keys
    }


def test_custom_definition_metadata():
    dbt_assets_custom = load_assets_from_dbt_manifest(
        manifest_json=manifest_json,
        node_info_to_definition_metadata_fn=lambda node_info: {
            "foo_key": node_info["name"],
            "bar_key": 1.0,
        },
    )

    for asset_key, custom_metadata in dbt_assets_custom[0].metadata_by_key.items():
        assert custom_metadata.get("table_schema") is None
        assert custom_metadata["foo_key"] == asset_key.path[-1]
        assert custom_metadata["bar_key"] == 1.0


def test_partitions(dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir):
    def _partition_key_to_vars(partition_key: str):
        if partition_key == "2022-01-02":
            return {"fail_test": True}
        else:
            return {"fail_test": False}

    dbt_assets = load_assets_from_dbt_project(
        test_project_dir,
        dbt_config_dir,
        use_build_command=True,
        partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
        partition_key_to_vars_fn=_partition_key_to_vars,
        # FreshnessPolicies not currently supported for partitioned assets
        node_info_to_freshness_policy_fn=lambda _: None,
    )

    result = materialize_to_memory(
        dbt_assets,
        partition_key="2022-01-01",
        resources={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    )
    assert result.success

    with pytest.raises(DagsterDbtCliRuntimeError):
        result = materialize_to_memory(
            dbt_assets,
            partition_key="2022-01-02",
            resources={
                "dbt": dbt_cli_resource_factory(
                    project_dir=test_project_dir, profiles_dir=dbt_config_dir
                )
            },
        )


@pytest.mark.parametrize(
    "prefix",
    [
        None,
        "snowflake",
        ["snowflake", "dbt_schema"],
    ],
)
@pytest.mark.parametrize("use_build", [True, False])
def test_select_from_project(
    dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir, use_build, prefix
):
    dbt_assets = load_assets_from_dbt_project(
        test_project_dir,
        dbt_config_dir,
        select="sort_by_calories subdir.least_caloric",
        use_build_command=use_build,
        key_prefix=prefix,
    )

    if prefix is None:
        prefix = []
    elif isinstance(prefix, str):
        prefix = [prefix]
    assert dbt_assets[0].keys == {
        AssetKey(prefix + suffix)
        for suffix in (["sort_by_calories"], ["subdir_schema", "least_caloric"])
    }

    assert dbt_assets[0].op.name == "run_dbt_5ad73_e4753"

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    ).execute_in_process()

    assert result.success
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 2
    observations = [
        event.event_specific_data.asset_observation
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_OBSERVATION"
    ]
    if use_build:
        assert len(observations) == 16
    else:
        assert len(observations) == 0


def test_multiple_select_from_project(dbt_seed, test_project_dir, dbt_config_dir):
    dbt_assets_a = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, select="sort_by_calories subdir.least_caloric"
    )

    dbt_assets_b = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, select="sort_by_calories"
    )

    @repository
    def foo():
        return [
            *with_resources(
                # dbt_assets_b is a subset of dbt_assets_a
                [*dbt_assets_a],
                resource_defs={"dbt": dbt_cli_resource},
            ),
            define_asset_job("a", dbt_assets_a),
            define_asset_job("b", dbt_assets_b),
        ]

    assert len(foo.get_all_jobs()) == 3


def test_dbt_ls_fail_fast():
    with pytest.raises(DagsterDbtCliFatalRuntimeError, match=r"Invalid.*--project-dir"):
        load_assets_from_dbt_project("bad_project_dir", "bad_config_dir")


@pytest.mark.parametrize("use_build", [True, False])
def test_select_from_manifest(
    dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir, use_build
):
    dbt_assets = load_assets_from_dbt_manifest(
        manifest_json,
        selected_unique_ids={
            "model.dagster_dbt_test_project.sort_by_calories",
            "model.dagster_dbt_test_project.least_caloric",
        },
        use_build_command=use_build,
    )

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    ).execute_in_process()

    assert result.success
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 2
    observations = [
        event.event_specific_data.asset_observation
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_OBSERVATION"
    ]
    if use_build:
        assert len(observations) == 16
    else:
        assert len(observations) == 0


@pytest.mark.parametrize("use_build", [True, False])
def test_node_info_to_asset_key(
    dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir, use_build
):
    dbt_assets = load_assets_from_dbt_project(
        test_project_dir,
        dbt_config_dir,
        node_info_to_asset_key=lambda node_info: AssetKey(["foo", node_info["name"]]),
        use_build_command=use_build,
    )
    assert get_asset_key_for_model(dbt_assets, "sort_hot_cereals_by_calories") == AssetKey(
        ["foo", "sort_hot_cereals_by_calories"]
    )

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    ).execute_in_process()

    assert result.success
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    if use_build:
        assert len(materializations) == 6
        assert materializations[0].asset_key == AssetKey(["foo", "cereals"])
    else:
        assert len(materializations) == 4
        assert materializations[0].asset_key == AssetKey(["foo", "sort_by_calories"])
    observations = [
        event.event_specific_data.asset_observation
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_OBSERVATION"
    ]
    if use_build:
        assert len(observations) == 17
    else:
        assert len(observations) == 0


def test_dagster_dbt_translator(
    dbt_seed, dbt_cli_resource_factory, test_project_dir, dbt_config_dir
):
    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        @classmethod
        def get_asset_key(cls, dbt_resource_props):
            return AssetKey(["foo", dbt_resource_props["name"]])

        @classmethod
        def get_metadata(cls, dbt_resource_props):
            return {"name_metadata": dbt_resource_props["name"] + "_metadata"}

        @classmethod
        def get_group_name(cls, dbt_resource_props):
            return "foo_group" if dbt_resource_props["name"] == "cereals" else None

        @classmethod
        def get_freshness_policy(cls, dbt_resource_props):
            return FreshnessPolicy(maximum_lag_minutes=1)

        @classmethod
        def get_auto_materialize_policy(cls, dbt_resource_props):
            return AutoMaterializePolicy.lazy()

    dbt_assets = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, dagster_dbt_translator=CustomDagsterDbtTranslator()
    )

    assert dbt_assets[0].keys == {
        AssetKey(["foo", "cereals"]),
        AssetKey(["foo", "least_caloric"]),
        AssetKey(["foo", "orders_snapshot"]),
        AssetKey(["foo", "sort_by_calories"]),
        AssetKey(["foo", "sort_cold_cereals_by_calories"]),
        AssetKey(["foo", "sort_hot_cereals_by_calories"]),
    }
    assert (
        dbt_assets[0].metadata_by_key[AssetKey(["foo", "cereals"])]["name_metadata"]
        == "cereals_metadata"
    )
    assert dbt_assets[0].group_names_by_key[AssetKey(["foo", "cereals"])] == "foo_group"
    assert dbt_assets[0].group_names_by_key[AssetKey(["foo", "least_caloric"])] == "default"

    for freshness_policy in dbt_assets[0].freshness_policies_by_key.values():
        assert freshness_policy == FreshnessPolicy(maximum_lag_minutes=1)

    for auto_materialize_policy in dbt_assets[0].auto_materialize_policies_by_key.values():
        assert auto_materialize_policy == AutoMaterializePolicy.lazy()

    result = materialize_to_memory(
        dbt_assets,
        resources={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    )

    assert result.success
    materializations = result.asset_materializations_for_node(dbt_assets[0].op.name)
    assert len(materializations) == 6
    assert materializations[0].asset_key == AssetKey(["foo", "cereals"])
    observations = result.asset_observations_for_node(dbt_assets[0].op.name)
    assert len(observations) == 17


@pytest.mark.parametrize(
    "job_selection,expected_asset_names",
    [
        (
            "*",
            (
                "sort_by_calories,cold_schema/sort_cold_cereals_by_calories,"
                "sort_hot_cereals_by_calories,subdir_schema/least_caloric,hanger1,hanger2,cereals,"
                "orders_snapshot"
            ),
        ),
        (
            "sort_by_calories+",
            (
                "sort_by_calories,subdir_schema/least_caloric,cold_schema/sort_cold_cereals_by_calories,"
                "sort_hot_cereals_by_calories,hanger1,orders_snapshot"
            ),
        ),
        ("*hanger2", "cereals,hanger2,subdir_schema/least_caloric,sort_by_calories"),
        (
            [
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
            ],
            "cold_schema/sort_cold_cereals_by_calories,subdir_schema/least_caloric",
        ),
    ],
)
def test_subsetting(
    dbt_build,
    dbt_cli_resource_factory,
    test_project_dir,
    dbt_config_dir,
    job_selection,
    expected_asset_names,
):
    dbt_assets = load_assets_from_dbt_project(test_project_dir, dbt_config_dir)

    @asset(deps=[AssetKey("sort_by_calories")])
    def hanger1():
        return None

    @asset(deps=[AssetKey(["subdir_schema", "least_caloric"])])
    def hanger2():
        return None

    result = (
        Definitions(
            assets=[*dbt_assets, hanger1, hanger2],
            resources={
                "dbt": dbt_cli_resource_factory(
                    project_dir=test_project_dir, profiles_dir=dbt_config_dir
                )
            },
            jobs=[define_asset_job("dbt_job", job_selection)],
        )
        .get_job_def("dbt_job")
        .execute_in_process()
    )

    assert result.success
    all_keys = {
        event.event_specific_data.materialization.asset_key
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    }
    expected_keys = {AssetKey(name.split("/")) for name in expected_asset_names.split(",")}
    assert all_keys == expected_keys


@pytest.mark.parametrize(
    "config,expected_asset_names",
    [
        ({"exclude": "tag:not_a_tag"}, "ALL"),
        (
            {"select": "sort_by_calories"},
            "sort_by_calories",
        ),
        ({"full-refresh": True}, "ALL"),
        ({"vars": {"my_var": "my_value", "another_var": 3, "a_third_var": True}}, "ALL"),
    ],
)
def test_op_config(
    config,
    expected_asset_names,
    dbt_seed,
    dbt_cli_resource_factory,
    test_project_dir,
    dbt_config_dir,
):
    if expected_asset_names == "ALL":
        expected_asset_names = (
            "sort_by_calories,cold_schema/sort_cold_cereals_by_calories,"
            "sort_hot_cereals_by_calories,subdir_schema/least_caloric,cereals,orders_snapshot"
        )

    dbt_assets = load_assets_from_dbt_manifest(manifest_json)
    result = materialize_to_memory(
        assets=dbt_assets,
        run_config={"ops": {"run_dbt_5ad73": {"config": config}}},
        resources={
            "dbt": dbt_cli_resource_factory(
                project_dir=test_project_dir, profiles_dir=dbt_config_dir
            )
        },
    )
    assert result.success
    all_keys = {
        event.event_specific_data.materialization.asset_key
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    }
    expected_keys = {AssetKey(name.split("/")) for name in expected_asset_names.split(",")}
    assert all_keys == expected_keys


def test_op_custom_name():
    instances = [{"target": "target_a"}, {"target": "target_b"}]
    dbt_assets = []
    for instance in instances:
        dbt_assets.extend(
            load_assets_from_dbt_manifest(
                manifest_json=manifest_json,
                key_prefix=[instance["target"], "duckdb", "test-schema"],
                op_name=f"{instance['target']}_dbt_op",
                select="fqn:* fqn:*",  # just a non-default selection
            )
        )
    op_names = [asset_group.op.name for asset_group in dbt_assets]
    assert len(op_names) == len(set(op_names)), (
        "Multiple instances of a dbt project cannot have the same op name.\n"
        f"dbt targets were: {instances}\n"
        f"op names generated were: {op_names}"
    )
    assert set(op_names) == {"target_a_dbt_op", "target_b_dbt_op"}


@pytest.mark.parametrize("load_from_manifest", [True, False])
@pytest.mark.parametrize(
    "select,exclude,expected_asset_names",
    [
        (
            "fqn:*",
            None,
            {
                "cereals",
                "orders_snapshot",
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
            },
        ),
        (
            "+least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric", "cereals"},
        ),
        (
            "sort_by_calories least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric"},
        ),
        (
            "tag:bar+",
            None,
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
            },
        ),
        (
            "tag:foo",
            None,
            {"sort_by_calories", "cold_schema/sort_cold_cereals_by_calories"},
        ),
        (
            "tag:foo,tag:bar",
            None,
            {"sort_by_calories"},
        ),
        (
            None,
            "sort_hot_cereals_by_calories",
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "cereals",
                "orders_snapshot",
            },
        ),
        (
            None,
            "+least_caloric",
            {
                "cold_schema/sort_cold_cereals_by_calories",
                "orders_snapshot",
                "sort_hot_cereals_by_calories",
            },
        ),
        (
            None,
            "sort_by_calories least_caloric",
            {
                "cold_schema/sort_cold_cereals_by_calories",
                "sort_hot_cereals_by_calories",
                "cereals",
                "orders_snapshot",
            },
        ),
        (
            None,
            "tag:foo",
            {
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "cereals",
                "orders_snapshot",
            },
        ),
    ],
)
def test_dbt_selections(
    dbt_build,
    test_project_dir,
    dbt_cli_resource_factory,
    dbt_config_dir,
    load_from_manifest,
    select,
    exclude,
    expected_asset_names,
):
    if load_from_manifest:
        dbt_assets = load_assets_from_dbt_manifest(manifest_json, select=select, exclude=exclude)
    else:
        dbt_assets = load_assets_from_dbt_project(
            project_dir=test_project_dir,
            profiles_dir=dbt_config_dir,
            select=select,
            exclude=exclude,
        )

    expected_asset_keys = {AssetKey(key.split("/")) for key in expected_asset_names}
    assert dbt_assets[0].keys == expected_asset_keys

    result = (
        Definitions(
            assets=dbt_assets,
            resources={
                "dbt": dbt_cli_resource_factory(
                    project_dir=test_project_dir, profiles_dir=dbt_config_dir
                )
            },
            jobs=[define_asset_job("dbt_job")],
        )
        .get_job_def("dbt_job")
        .execute_in_process()
    )

    assert result.success
    all_keys = {
        event.event_specific_data.materialization.asset_key
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    }
    assert all_keys == expected_asset_keys


@pytest.mark.parametrize(
    "select,error_match",
    [
        ("tag:nonexist", r"(No dbt models match|does not match any nodes)"),
        ("asjdlhalskujh:z", "not a valid method name"),
    ],
)
def test_static_select_invalid_selection(select, error_match):
    with pytest.raises(Exception, match=error_match):
        load_assets_from_dbt_manifest(manifest_json, select=select)


def test_source_key_prefix(test_python_project_dir, dbt_python_config_dir):
    dbt_assets = load_assets_from_dbt_project(
        test_python_project_dir,
        dbt_python_config_dir,
        key_prefix="dbt",
        source_key_prefix="source",
    )
    assert dbt_assets[0].keys_by_input_name == {
        "source_dagster_dbt_python_test_project_dagster_bot_labeled_users": AssetKey(
            ["source", "dagster", "bot_labeled_users"]
        ),
        "source_dagster_dbt_python_test_project_raw_data_events": AssetKey(
            ["source", "raw_data", "events"]
        ),
        "source_dagster_dbt_python_test_project_raw_data_users": AssetKey(
            ["source", "raw_data", "users"]
        ),
    }

    assert dbt_assets[0].keys_by_output_name["cleaned_users"] == AssetKey(["dbt", "cleaned_users"])


def test_source_tag_selection(test_python_project_dir, dbt_python_config_dir):
    dbt_assets = load_assets_from_dbt_project(
        test_python_project_dir, dbt_python_config_dir, select="tag:events"
    )

    assert len(dbt_assets[0].keys) == 2

    test_python_manifest_path = os.path.join(test_python_project_dir, "target", "manifest.json")
    with open(test_python_manifest_path, "r", encoding="utf8") as f:
        test_python_manifest_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(test_python_manifest_json, select="tag:events")

    assert len(dbt_assets[0].keys) == 2


def test_python_interleaving(
    dbt_cli_resource_factory, test_python_project_dir, dbt_python_config_dir
):
    dbt_assets = load_assets_from_dbt_project(
        test_python_project_dir, dbt_python_config_dir, key_prefix="test_python_schema"
    )

    duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

    @asset(key_prefix="raw_data")
    def events():
        return read_csv(os.path.join(test_python_project_dir, "events.csv"))

    @asset(key_prefix="raw_data")
    def users():
        return read_csv(os.path.join(test_python_project_dir, "users.csv"))

    @asset(key_prefix="dagster", ins={"cleaned_users": AssetIn(key_prefix="test_python_schema")})
    def bot_labeled_users(cleaned_users):
        # super advanced bot labeling algorithm
        bot_labeled_users_df = cleaned_users.copy()
        bot_labeled_users_df["is_bot"] = bot_labeled_users_df["user_id"].apply(lambda x: x % 5 == 0)
        bot_labeled_users_df = bot_labeled_users_df.drop(columns=["day"])

        return bot_labeled_users_df

    job_def = Definitions(
        assets=[*dbt_assets, users, events, bot_labeled_users],
        resources={
            "io_manager": duckdb_io_manager.configured(
                {"database": os.path.join(test_python_project_dir, "test.duckdb")}
            ),
            "dbt": dbt_cli_resource_factory(
                project_dir=test_python_project_dir, profiles_dir=dbt_python_config_dir
            ),
        },
        jobs=[define_asset_job("interleave_job")],
    ).get_job_def("interleave_job")

    result = job_def.execute_in_process()
    assert result.success
    all_keys = {
        event.event_specific_data.materialization.asset_key
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    }
    expected_asset_names = [
        "test_python_schema.cleaned_events",
        "test_python_schema.cleaned_users",
        "test_python_schema.daily_aggregated_events",
        "test_python_schema.daily_aggregated_users",
        "dagster.bot_labeled_users",
        "test_python_schema.bot_labeled_events",
        "raw_data.events",
        "raw_data.users",
    ]
    expected_keys = {AssetKey(name.split(".")) for name in expected_asset_names}
    assert all_keys == expected_keys
