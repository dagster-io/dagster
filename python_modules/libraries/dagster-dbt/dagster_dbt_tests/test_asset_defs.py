import json
from unittest.mock import MagicMock

import pytest
from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest, load_assets_from_dbt_project
from dagster_dbt.errors import DagsterDbtCliFatalRuntimeError
from dagster_dbt.types import DbtOutput

from dagster import AssetGroup, AssetKey, MetadataEntry, ResourceDefinition, asset, repository
from dagster.core.asset_defs import build_assets_job
from dagster.utils import file_relative_path


def test_load_from_manifest_json():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    run_results_path = file_relative_path(__file__, "sample_run_results.json")
    with open(run_results_path, "r", encoding="utf8") as f:
        run_results_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    assert_assets_match_project(dbt_assets)

    dbt = MagicMock()
    dbt.get_run_results_json.return_value = run_results_json
    dbt.run.return_value = DbtOutput(run_results_json)
    dbt.build.return_value = DbtOutput(run_results_json)
    dbt.get_manifest_json.return_value = manifest_json
    assets_job = build_assets_job(
        "assets_job",
        dbt_assets,
        resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)},
    )
    assert assets_job.execute_in_process().success


def test_runtime_metadata_fn():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    run_results_path = file_relative_path(__file__, "sample_run_results.json")
    with open(run_results_path, "r", encoding="utf8") as f:
        run_results_json = json.load(f)

    def runtime_metadata_fn(context, node_info):
        return {"op_name": context.solid_def.name, "dbt_model": node_info["name"]}

    dbt_assets = load_assets_from_dbt_manifest(
        manifest_json=manifest_json, runtime_metadata_fn=runtime_metadata_fn
    )
    assert_assets_match_project(dbt_assets)

    dbt = MagicMock()
    dbt.run.return_value = DbtOutput(run_results_json)
    dbt.build.return_value = DbtOutput(run_results_json)
    dbt.get_manifest_json.return_value = manifest_json
    assets_job = build_assets_job(
        "assets_job",
        dbt_assets,
        resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)},
    )
    result = assets_job.execute_in_process()
    assert result.success

    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 4
    assert materializations[0].metadata_entries == [
        MetadataEntry("op_name", value=dbt_assets[0].op.name),
        MetadataEntry("dbt_model", value=materializations[0].asset_key.path[-1]),
    ]


def assert_assets_match_project(dbt_assets):
    assert len(dbt_assets) == 1
    assets_op = dbt_assets[0].op
    assert assets_op.tags == {"kind": "dbt"}
    assert len(assets_op.input_defs) == 0
    assert set(assets_op.output_dict.keys()) == {
        "sort_by_calories",
        "least_caloric",
        "sort_hot_cereals_by_calories",
        "sort_cold_cereals_by_calories",
    }
    for model_name in [
        "least_caloric",
        "sort_hot_cereals_by_calories",
        "sort_cold_cereals_by_calories",
    ]:
        assert dbt_assets[0].asset_keys_by_output_name[model_name] == AssetKey(
            ["test-schema", model_name]
        )
        assert dbt_assets[0].asset_deps[AssetKey(["test-schema", model_name])] == {
            AssetKey(["test-schema", "sort_by_calories"])
        }

    assert dbt_assets[0].asset_keys_by_output_name["sort_by_calories"] == AssetKey(
        ["test-schema", "sort_by_calories"]
    )
    assert not dbt_assets[0].asset_deps[AssetKey(["test-schema", "sort_by_calories"])]


def test_fail_immediately(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir
):  # pylint: disable=unused-argument
    from dagster import build_init_resource_context

    dbt_assets = load_assets_from_dbt_project(test_project_dir, dbt_config_dir)
    good_dbt = dbt_cli_resource.configured(
        {
            "project_dir": test_project_dir,
            "profiles_dir": dbt_config_dir,
        }
    )

    # ensure that there will be a run results json
    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={"dbt": good_dbt},
    ).execute_in_process()

    assert good_dbt(build_init_resource_context()).get_run_results_json()

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource.configured(
                {
                    "project_dir": test_project_dir,
                    "profiles_dir": "BAD PROFILES DIR",
                }
            )
        },
    ).execute_in_process(raise_on_error=False)

    assert not result.success
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 0


@pytest.mark.parametrize("use_build, fail_test", [(True, False), (True, True), (False, False)])
def test_basic(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir, use_build, fail_test
):  # pylint: disable=unused-argument

    dbt_assets = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, use_build_command=use_build
    )

    assert dbt_assets[0].op.name == "run_dbt_dagster_dbt_test_project"

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource.configured(
                {
                    "project_dir": test_project_dir,
                    "profiles_dir": dbt_config_dir,
                    "vars": {"fail_test": fail_test},
                }
            )
        },
    ).execute_in_process(raise_on_error=False)

    assert result.success == (not fail_test)
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    if fail_test:
        # the test will fail after the first model is completed, so others will not be emitted
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey(["test-schema", "sort_by_calories"])
    else:
        assert len(materializations) == 4
    observations = [
        event.event_specific_data.asset_observation
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_OBSERVATION"
    ]
    if use_build:
        assert len(observations) == 17
    else:
        assert len(observations) == 0


@pytest.mark.parametrize("use_build", [True, False])
def test_select_from_project(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir, use_build
):  # pylint: disable=unused-argument

    dbt_assets = load_assets_from_dbt_project(
        test_project_dir,
        dbt_config_dir,
        select="sort_by_calories subdir.least_caloric",
        use_build_command=use_build,
    )

    assert dbt_assets[0].op.name == "run_dbt_dagster_dbt_test_project_e4753"

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource.configured(
                {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
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


def test_multiple_select_from_project(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir
):  # pylint: disable=unused-argument

    dbt_assets_a = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, select="sort_by_calories subdir.least_caloric"
    )

    dbt_assets_b = load_assets_from_dbt_project(
        test_project_dir, dbt_config_dir, select="sort_by_calories"
    )

    @repository
    def foo():
        return [
            AssetGroup(dbt_assets_a, resource_defs={"dbt": dbt_cli_resource}).build_job("a"),
            AssetGroup(dbt_assets_b, resource_defs={"dbt": dbt_cli_resource}).build_job("b"),
        ]

    assert len(foo.get_all_jobs()) == 2


def test_dbt_ls_fail_fast():
    with pytest.raises(DagsterDbtCliFatalRuntimeError):
        load_assets_from_dbt_project("bad_project_dir", "bad_config_dir")


@pytest.mark.parametrize("use_build", [True, False])
def test_select_from_manifest(
    dbt_seed, conn_string, test_project_dir, dbt_config_dir, use_build
):  # pylint: disable=unused-argument

    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)
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
            "dbt": dbt_cli_resource.configured(
                {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
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
    dbt_seed, conn_string, test_project_dir, dbt_config_dir, use_build
):  # pylint: disable=unused-argument
    dbt_assets = load_assets_from_dbt_project(
        test_project_dir,
        dbt_config_dir,
        node_info_to_asset_key=lambda node_info: AssetKey(["foo", node_info["name"]]),
        use_build_command=use_build,
    )

    result = build_assets_job(
        "test_job",
        dbt_assets,
        resource_defs={
            "dbt": dbt_cli_resource.configured(
                {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
            )
        },
    ).execute_in_process()

    assert result.success
    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
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


@pytest.mark.parametrize(
    "job_selection,expected_asset_names",
    [
        (
            "*",
            "sort_by_calories,sort_cold_cereals_by_calories,sort_hot_cereals_by_calories,least_caloric,hanger1,hanger2",
        ),
        (
            "test-schema>sort_by_calories+",
            "sort_by_calories,least_caloric,sort_cold_cereals_by_calories,sort_hot_cereals_by_calories,hanger1",
        ),
        ("*test-schema>hanger2", "hanger2,least_caloric,sort_by_calories"),
        (
            ["test-schema>sort_cold_cereals_by_calories", "test-schema>least_caloric"],
            "sort_cold_cereals_by_calories,least_caloric",
        ),
    ],
)
def test_subsetting(
    dbt_build,
    conn_string,
    test_project_dir,
    dbt_config_dir,
    job_selection,
    expected_asset_names,
):  # pylint: disable=unused-argument

    dbt_assets = load_assets_from_dbt_project(test_project_dir, dbt_config_dir)

    @asset(namespace="test-schema")
    def hanger1(sort_by_calories):
        return None

    @asset(namespace="test-schema")
    def hanger2(least_caloric):
        return None

    result = (
        AssetGroup(
            dbt_assets + [hanger1, hanger2],
            resource_defs={
                "dbt": dbt_cli_resource.configured(
                    {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
                )
            },
        )
        .build_job(name="dbt_job", selection=job_selection)
        .execute_in_process()
    )

    assert result.success
    all_keys = {
        event.event_specific_data.materialization.asset_key
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    }
    expected_keys = {AssetKey(["test-schema", name]) for name in expected_asset_names.split(",")}
    assert all_keys == expected_keys


@pytest.mark.parametrize("load_from_manifest", [True, False])
@pytest.mark.parametrize(
    "select,expected_asset_names",
    [
        (
            "*",
            {
                "sort_by_calories",
                "sort_cold_cereals_by_calories",
                "least_caloric",
                "sort_hot_cereals_by_calories",
            },
        ),
        (
            "+least_caloric",
            {"sort_by_calories", "least_caloric"},
        ),
        (
            "sort_by_calories least_caloric",
            {"sort_by_calories", "least_caloric"},
        ),
        (
            "tag:bar+",
            {
                "sort_by_calories",
                "sort_cold_cereals_by_calories",
                "least_caloric",
                "sort_hot_cereals_by_calories",
            },
        ),
        (
            "tag:foo",
            {"sort_by_calories", "sort_cold_cereals_by_calories"},
        ),
        (
            "tag:foo,tag:bar",
            {"sort_by_calories"},
        ),
    ],
)
def test_dbt_selects(
    dbt_build,
    conn_string,
    test_project_dir,
    dbt_config_dir,
    load_from_manifest,
    select,
    expected_asset_names,
):  # pylint: disable=unused-argument
    if load_from_manifest:
        manifest_path = file_relative_path(__file__, "sample_manifest.json")
        with open(manifest_path, "r", encoding="utf8") as f:
            manifest_json = json.load(f)

        dbt_assets = load_assets_from_dbt_manifest(manifest_json, select=select)
    else:
        dbt_assets = load_assets_from_dbt_project(
            project_dir=test_project_dir, profiles_dir=dbt_config_dir, select=select
        )

    expected_asset_keys = {AssetKey(["test-schema", key]) for key in expected_asset_names}
    assert dbt_assets[0].asset_keys == expected_asset_keys

    result = (
        AssetGroup(
            dbt_assets,
            resource_defs={
                "dbt": dbt_cli_resource.configured(
                    {"project_dir": test_project_dir, "profiles_dir": dbt_config_dir}
                )
            },
        )
        .build_job(name="dbt_job")
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
    [("tag:nonexist", "No dbt models match"), ("asjdlhalskujh:z", "not a valid method name")],
)
def test_static_select_invalid_selection(select, error_match):
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    with pytest.raises(Exception, match=error_match):
        load_assets_from_dbt_manifest(manifest_json, select=select)
