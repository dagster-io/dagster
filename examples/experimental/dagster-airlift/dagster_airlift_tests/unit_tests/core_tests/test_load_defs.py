from typing import cast

import mock
from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    asset,
    asset_check,
    executor,
    job,
    logger,
    multi_asset,
    schedule,
    sensor,
)
from dagster._core.definitions.asset_dep import AssetDep
from dagster._serdes.serdes import deserialize_value
from dagster._utils.test.definitions import (
    scoped_reconstruction_metadata,
    unwrap_reconstruction_metadata,
)
from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core import (
    build_defs_from_airflow_instance as build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance
from dagster_airlift.core.multiple_tasks import targeted_by_multiple_tasks
from dagster_airlift.core.serialization.compute import (
    build_airlift_metadata_mapping_info,
    compute_serialized_data,
)
from dagster_airlift.core.serialization.defs_construction import (
    key_for_automapped_task_asset,
    make_default_dag_asset_key,
)
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAirflowDefinitionsData,
    TaskHandle,
)
from dagster_airlift.core.top_level_dag_def_api import assets_with_task_mappings
from dagster_airlift.core.utils import is_task_mapped_asset_spec, metadata_for_task_mapping
from dagster_airlift.test import make_instance

from dagster_airlift_tests.unit_tests.conftest import (
    assert_dependency_structure_in_assets,
    fully_loaded_repo_from_airflow_asset_graph,
    load_definitions_airflow_asset_graph,
)


@executor
def nonstandard_executor(init_context):
    pass


@logger
def nonstandard_logger(init_context):
    pass


@sensor(job_name="the_job")
def some_sensor():
    pass


@schedule(cron_schedule="0 0 * * *", job_name="the_job")
def some_schedule():
    pass


@asset
def a():
    pass


b_spec = AssetSpec(key="b")


@asset_check(asset=a)
def a_check():
    pass


@job
def the_job():
    pass


def make_test_dag_asset_key(dag_id: str) -> AssetKey:
    return make_default_dag_asset_key("test_instance", dag_id)


def test_defs_passthrough() -> None:
    """Test that passed-through definitions are present in the final definitions."""
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance({"dag": ["task"]}),
        defs=Definitions(
            assets=[a, b_spec],
            asset_checks=[a_check],
            jobs=[the_job],
            sensors=[some_sensor],
            schedules=[some_schedule],
            loggers={"the_logger": nonstandard_logger},
            executor=nonstandard_executor,
        ),
    )
    assert defs.executor == nonstandard_executor
    assert defs.loggers
    assert len(defs.loggers) == 1
    assert next(iter(defs.loggers.keys())) == "the_logger"
    assert defs.sensors
    assert len(list(defs.sensors)) == 2
    our_sensor = next(
        iter(sensor_def for sensor_def in defs.sensors if sensor_def.name == "some_sensor")
    )
    assert our_sensor == some_sensor
    assert defs.schedules
    assert len(list(defs.schedules)) == 1
    assert next(iter(defs.schedules)) == some_schedule
    assert defs.jobs
    assert len(list(defs.jobs)) == 1
    assert next(iter(defs.jobs)) == the_job
    repo = defs.get_repository_def()
    # Ensure that asset specs get properly coerced into asset defs
    assert set(repo.assets_defs_by_key.keys()) == {
        a.key,
        b_spec.key,
        make_test_dag_asset_key("dag"),
    }
    assert isinstance(repo.assets_defs_by_key[b_spec.key], AssetsDefinition)


def test_coerce_specs() -> None:
    """Test that asset specs are properly coerced into asset keys."""
    # Initialize an airflow instance with a dag "dag", which contains a task "task". There are no task instances or runs.

    spec = AssetSpec(key="a", metadata=metadata_for_task_mapping(task_id="task", dag_id="dag"))
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance({"dag": ["task"]}),
        defs=Definitions(
            assets=[spec],
        ),
    )
    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) == 2
    assert AssetKey("a") in repo.assets_defs_by_key
    assets_def = repo.assets_defs_by_key[AssetKey("a")]
    # Asset metadata properties have been glommed onto the asset
    spec = next(iter(assets_def.specs))
    assert spec.metadata["Dag ID"] == "dag"


def test_invalid_dagster_named_tasks_and_dags() -> None:
    """Test that invalid dagster names are converted to valid names."""
    a = AssetKey("a")
    spec = AssetSpec(
        key=a,
        metadata=metadata_for_task_mapping(task_id="task-with-hyphens", dag_id="dag-with-hyphens"),
    )
    airflow_instance = make_instance({"dag-with-hyphens": ["task-with-hyphens"]})
    defs = build_defs_from_airflow_instance(
        airflow_instance=airflow_instance,
        defs=Definitions(
            assets=[spec],
        ),
    )

    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) == 2
    assert a in repo.assets_defs_by_key
    assets_def = repo.assets_defs_by_key[a]
    assert not assets_def.is_executable

    assert make_test_dag_asset_key("dag-with-hyphens") in repo.assets_defs_by_key
    dag_def = repo.assets_defs_by_key[
        make_default_dag_asset_key(airflow_instance.name, "dag_with_hyphens")
    ]
    assert not dag_def.is_executable


def has_single_task_handle(spec: AssetSpec, dag_id: str, task_id: str):
    assert len(spec.metadata[TASK_MAPPING_METADATA_KEY]) == 1
    task_handle_dict = next(iter(spec.metadata[TASK_MAPPING_METADATA_KEY]))
    return task_handle_dict["dag_id"] == dag_id and task_handle_dict["task_id"] == task_id


def test_transitive_asset_deps() -> None:
    """Test that cross-dag transitive asset dependencies are correctly generated."""
    # Asset graph is a -> b -> c where a and c are in different dags, and b isn't in any dag.
    repo_def = fully_loaded_repo_from_airflow_asset_graph(
        assets_per_task={
            "dag1": {"task": [("a", [])]},
            "dag2": {"task": [("c", ["b"])]},
        },
        additional_defs=Definitions(assets=[AssetSpec(key="b", deps=["a"])]),
    )
    repo_def.load_all_definitions()
    airflow_instance = make_instance(dag_and_task_structure={"dag1": ["task"], "dag2": ["task"]})
    dag1_key = make_default_dag_asset_key(instance_name=airflow_instance.name, dag_id="dag1")
    dag2_key = make_default_dag_asset_key(instance_name=airflow_instance.name, dag_id="dag2")
    a_key = AssetKey(["a"])
    b_key = AssetKey(["b"])
    c_key = AssetKey(["c"])
    assert len(repo_def.assets_defs_by_key) == 5
    assert set(repo_def.assets_defs_by_key.keys()) == {
        dag1_key,
        dag2_key,
        a_key,
        b_key,
        c_key,
    }

    dag1_asset = repo_def.assets_defs_by_key[dag1_key]
    assert [dep.asset_key for dep in next(iter(dag1_asset.specs)).deps] == [a_key]

    dag2_asset = repo_def.assets_defs_by_key[dag2_key]
    assert [dep.asset_key for dep in next(iter(dag2_asset.specs)).deps] == [c_key]

    a_asset = repo_def.assets_defs_by_key[a_key]
    assert [dep.asset_key for dep in next(iter(a_asset.specs)).deps] == []
    assert has_single_task_handle(next(iter(a_asset.specs)), "dag1", "task")

    b_asset = repo_def.assets_defs_by_key[b_key]
    assert [dep.asset_key for dep in next(iter(b_asset.specs)).deps] == [a_key]
    assert not is_task_mapped_asset_spec(next(iter(b_asset.specs)))

    c_asset = repo_def.assets_defs_by_key[c_key]
    assert [dep.asset_key for dep in next(iter(c_asset.specs)).deps] == [b_key]
    assert has_single_task_handle(next(iter(c_asset.specs)), "dag2", "task")


def test_peered_dags() -> None:
    """Test peered dags show up, and that linkage is preserved downstream of dags."""
    defs = load_definitions_airflow_asset_graph(
        assets_per_task={
            "dag1": {"task": []},
            "dag2": {"task": []},
            "dag3": {"task": []},
        },
        additional_defs=Definitions(
            assets=[AssetSpec(key="a", deps=[make_test_dag_asset_key("dag1")])]
        ),
    )
    assert defs.assets
    repo_def = defs.get_repository_def()
    repo_def.load_all_definitions()
    assert len(repo_def.assets_defs_by_key) == 4
    assert_dependency_structure_in_assets(
        repo_def=repo_def,
        expected_deps={
            make_test_dag_asset_key("dag1").to_user_string(): [],
            make_test_dag_asset_key("dag2").to_user_string(): [],
            make_test_dag_asset_key("dag3").to_user_string(): [],
            "a": [make_test_dag_asset_key("dag1").to_user_string()],
        },
    )


def test_observed_assets() -> None:
    """Test that observed assets are properly linked to dags."""
    # Asset graph structure:
    #   a
    #  / \
    # b   c
    #  \ /
    #   d
    #  / \
    # e   f
    defs = load_definitions_airflow_asset_graph(
        assets_per_task={
            "dag": {
                "task1": [("a", []), ("b", ["a"]), ("c", ["a"])],
                "task2": [("d", ["b", "c"]), ("e", ["d"]), ("f", ["d"])],
            },
        },
    )
    assert defs.assets
    repo_def = defs.get_repository_def()
    repo_def.load_all_definitions()
    repo_def.load_all_definitions()
    assert len(repo_def.assets_defs_by_key) == 7
    assert_dependency_structure_in_assets(
        repo_def=repo_def,
        expected_deps={
            "a": [],
            "b": ["a"],
            "c": ["a"],
            "d": ["b", "c"],
            "e": ["d"],
            "f": ["d"],
            # Only leaf assets should be immediately upstream of the dag
            make_test_dag_asset_key("dag").to_user_string(): ["e", "f"],
        },
    )


def test_local_airflow_instance() -> None:
    """Test that a local-backed airflow instance can be correctly peered, and errors when the correct info can't be found."""
    defs = load_definitions_airflow_asset_graph(
        assets_per_task={
            "dag": {"task": [("a", [])]},
        },
        create_assets_defs=True,
    )

    assert defs.assets
    repo_def = defs.get_repository_def()

    defs = load_definitions_airflow_asset_graph(
        assets_per_task={
            "dag": {"task": [("a", [])]},
        },
        create_assets_defs=True,
    )
    repo_def = defs.get_repository_def()
    assert defs.assets
    repo_def = defs.get_repository_def()
    assert len(repo_def.assets_defs_by_key) == 2


def test_cached_loading() -> None:
    """Test cached loading behavior."""
    a = AssetKey("a")
    spec = AssetSpec(
        key=a,
        metadata=metadata_for_task_mapping(task_id="task", dag_id="dag"),
    )
    instance = make_instance({"dag": ["task"]})
    passed_in_defs = Definitions(assets=[spec])

    defs = build_defs_from_airflow_instance(airflow_instance=instance, defs=passed_in_defs)
    assert defs.assets
    assert len(list(defs.assets)) == 2
    assert {
        key for assets_def in defs.assets for key in cast(AssetsDefinition, assets_def).keys
    } == {a, make_test_dag_asset_key("dag")}
    assert len(defs.metadata) == 1
    assert "dagster-airlift/source/test_instance" in defs.metadata
    assert isinstance(defs.metadata["dagster-airlift/source/test_instance"].value, str)
    assert isinstance(
        deserialize_value(defs.metadata["dagster-airlift/source/test_instance"].value),
        SerializedAirflowDefinitionsData,
    )

    with scoped_reconstruction_metadata(unwrap_reconstruction_metadata(defs)):
        with mock.patch(
            "dagster_airlift.core.serialization.compute.compute_serialized_data",
            wraps=compute_serialized_data,
        ) as mock_compute_serialized_data:
            reloaded_defs = build_defs_from_airflow_instance(
                airflow_instance=instance, defs=passed_in_defs
            )
            assert mock_compute_serialized_data.call_count == 0
            reloaded_defs = build_defs_from_airflow_instance(
                airflow_instance=instance, defs=passed_in_defs
            )
            assert reloaded_defs.assets
            assert len(list(reloaded_defs.assets)) == 2
            assert {
                key
                for assets_def in reloaded_defs.assets
                for key in cast(AssetsDefinition, assets_def).keys
            } == {a, make_test_dag_asset_key("dag")}
            assert len(reloaded_defs.metadata) == 1
            assert "dagster-airlift/source/test_instance" in reloaded_defs.metadata
            # Reconstruction data should remain the same.
            assert (
                reloaded_defs.metadata["dagster-airlift/source/test_instance"].value
                == defs.metadata["dagster-airlift/source/test_instance"].value
            )


def test_multiple_tasks_per_asset(init_load_context: None) -> None:
    """Test behavior for a single AssetsDefinition where different specs map to different airflow tasks/dags."""

    @multi_asset(
        specs=[
            AssetSpec(key="a", metadata=metadata_for_task_mapping(task_id="task1", dag_id="dag1")),
            AssetSpec(key="b", metadata=metadata_for_task_mapping(task_id="task2", dag_id="dag2")),
        ],
        name="multi_asset",
    )
    def my_asset():
        pass

    instance = make_instance({"dag1": ["task1"], "dag2": ["task2"]})
    defs = build_defs_from_airflow_instance(
        airflow_instance=instance,
        defs=Definitions(assets=[my_asset]),
    )
    assert defs.assets
    # 3 Full assets definitions, but 4 keys
    assert len(list(defs.assets)) == 3
    assert {
        key for assets_def in defs.assets for key in cast(AssetsDefinition, assets_def).keys
    } == {
        AssetKey("a"),
        AssetKey("b"),
        make_test_dag_asset_key("dag1"),
        make_test_dag_asset_key("dag2"),
    }
    repo_def = defs.get_repository_def()
    a_and_b_asset = repo_def.assets_defs_by_key[AssetKey("a")]
    a_spec = next(iter(spec for spec in a_and_b_asset.specs if spec.key == AssetKey("a")))
    assert has_single_task_handle(a_spec, "dag1", "task1")
    b_spec = next(iter(spec for spec in a_and_b_asset.specs if spec.key == AssetKey("b")))
    assert has_single_task_handle(b_spec, "dag2", "task2")


def test_multiple_tasks_to_single_asset_metadata() -> None:
    instance = make_instance({"dag1": ["task1"], "dag2": ["task2"]})

    @asset(
        metadata={
            TASK_MAPPING_METADATA_KEY: [
                {"dag_id": "dag1", "task_id": "task1"},
                {"dag_id": "dag2", "task_id": "task2"},
            ]
        }
    )
    def an_asset() -> None: ...

    defs = build_defs_from_airflow_instance(
        airflow_instance=instance, defs=Definitions(assets=[an_asset])
    )

    assert defs.assets
    assert len(list(defs.assets)) == 3  # two dags and one asset

    assert defs.get_asset_graph().assets_def_for_key(AssetKey("an_asset")).specs_by_key[
        AssetKey("an_asset")
    ].metadata[TASK_MAPPING_METADATA_KEY] == [
        {"dag_id": "dag1", "task_id": "task1"},
        {"dag_id": "dag2", "task_id": "task2"},
    ]


def test_automapped_build() -> None:
    airflow_instance = make_instance(
        dag_and_task_structure={"dag1": ["task1", "task2", "standalone"]},
        task_deps={"task1": ["task2"]},
    )
    defs = build_full_automapped_dags_from_airflow_instance(
        airflow_instance=airflow_instance,
    )

    dag1_task1 = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task1")
    dag1_task2 = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task2")
    dag1_standalone = key_for_automapped_task_asset(airflow_instance.name, "dag1", "standalone")

    specs = {spec.key: spec for spec in defs.get_all_asset_specs()}

    assert specs[dag1_task1].deps == []
    assert specs[dag1_task2].deps == [AssetDep(dag1_task1)]
    assert specs[dag1_standalone].deps == []

    assert make_test_dag_asset_key("dag1") in specs

    assert specs[dag1_task1].metadata["Dag ID"] == "dag1"
    assert specs[dag1_task1].metadata["Task ID"] == "task1"
    assert specs[dag1_task1].description == 'Automapped task in dag "dag1" with task_id "task1"'
    assert specs[dag1_task2].metadata["Dag ID"] == "dag1"
    assert specs[dag1_task2].metadata["Task ID"] == "task2"

    assert "dagster/kind/airflow" in specs[dag1_task1].tags
    assert "dagster/kind/task" in specs[dag1_task1].tags

    assert set(specs[make_test_dag_asset_key("dag1")].deps) == {
        AssetDep(dag1_standalone),
        AssetDep(dag1_task2),
    }


def test_multiple_tasks_dag_defs() -> None:
    @asset
    def other_asset() -> None: ...

    @asset(deps=[other_asset])
    def scheduled_twice() -> None: ...

    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance(
            {"weekly_dag": ["task1"], "daily_dag": ["task1"], "other_dag": ["task1"]}
        ),
        defs=Definitions.merge(
            dag_defs(
                "other_dag",
                task_defs(
                    "task1",
                    Definitions(assets=[other_asset]),
                ),
            ),
            targeted_by_multiple_tasks(
                Definitions([scheduled_twice]),
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "task1"},
                    {"dag_id": "daily_dag", "task_id": "task1"},
                ],
            ),
        ),
    )

    Definitions.validate_loadable(defs)


def test_mixed_multiple_tasks_single_task_mapping_defs_sep_dags() -> None:
    @asset
    def single_targeted_asset() -> None: ...

    @asset
    def double_targeted_asset() -> None: ...

    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance(
            {"weekly_dag": ["task1"], "daily_dag": ["task1"], "other_dag": ["task1"]}
        ),
        defs=Definitions.merge(
            dag_defs(
                "other_dag",
                task_defs(
                    "task1",
                    Definitions(assets=[single_targeted_asset]),
                ),
            ),
            targeted_by_multiple_tasks(
                Definitions([double_targeted_asset]),
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "task1"},
                    {"dag_id": "daily_dag", "task_id": "task1"},
                ],
            ),
        ),
    )

    Definitions.validate_loadable(defs)

    mapping_info = build_airlift_metadata_mapping_info(defs)
    assert mapping_info.all_mapped_asset_keys_by_dag_id["other_dag"] == {
        AssetKey("single_targeted_asset"),
    }
    assert mapping_info.all_mapped_asset_keys_by_dag_id["weekly_dag"] == {
        AssetKey("double_targeted_asset"),
    }
    assert mapping_info.all_mapped_asset_keys_by_dag_id["daily_dag"] == {
        AssetKey("double_targeted_asset"),
    }

    assert mapping_info.task_handle_map[AssetKey("single_targeted_asset")] == {
        TaskHandle(dag_id="other_dag", task_id="task1")
    }
    assert mapping_info.task_handle_map[AssetKey("double_targeted_asset")] == {
        TaskHandle(dag_id="weekly_dag", task_id="task1"),
        TaskHandle(dag_id="daily_dag", task_id="task1"),
    }


def test_mixed_multiple_task_single_task_mapping_same_dags() -> None:
    @asset
    def other_asset() -> None: ...

    @asset
    def double_targeted_asset() -> None: ...

    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance(
            {
                "weekly_dag": ["task1", "task_for_other_asset"],
                "daily_dag": ["task1"],
            }
        ),
        defs=Definitions.merge(
            targeted_by_multiple_tasks(
                Definitions([double_targeted_asset]),
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "task1"},
                    {"dag_id": "daily_dag", "task_id": "task1"},
                ],
            ),
            dag_defs(
                "weekly_dag",
                task_defs(
                    "task_for_other_asset",
                    Definitions(assets=[other_asset]),
                ),
            ),
        ),
    )

    Definitions.validate_loadable(defs)

    mapping_info = build_airlift_metadata_mapping_info(defs)
    assert mapping_info.all_mapped_asset_keys_by_dag_id["weekly_dag"] == {
        AssetKey("other_asset"),
        AssetKey("double_targeted_asset"),
    }
    assert mapping_info.all_mapped_asset_keys_by_dag_id["daily_dag"] == {
        AssetKey("double_targeted_asset"),
    }

    assert mapping_info.task_handle_map[AssetKey("other_asset")] == {
        TaskHandle(dag_id="weekly_dag", task_id="task_for_other_asset")
    }
    assert mapping_info.task_handle_map[AssetKey("double_targeted_asset")] == {
        TaskHandle(dag_id="weekly_dag", task_id="task1"),
        TaskHandle(dag_id="daily_dag", task_id="task1"),
    }


def test_mixed_multiple_task_single_task_mapping_same_task() -> None:
    @asset
    def other_asset() -> None: ...

    @asset
    def double_targeted_asset() -> None: ...

    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance(
            {
                "weekly_dag": ["task1"],
                "daily_dag": ["task1"],
            }
        ),
        defs=Definitions.merge(
            targeted_by_multiple_tasks(
                Definitions([double_targeted_asset]),
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "task1"},
                    {"dag_id": "daily_dag", "task_id": "task1"},
                ],
            ),
            dag_defs(
                "weekly_dag",
                task_defs(
                    "task1",
                    Definitions(assets=[other_asset]),
                ),
            ),
        ),
    )

    Definitions.validate_loadable(defs)

    mapping_info = build_airlift_metadata_mapping_info(defs)
    assert mapping_info.all_mapped_asset_keys_by_dag_id["weekly_dag"] == {
        AssetKey("other_asset"),
        AssetKey("double_targeted_asset"),
    }
    assert mapping_info.all_mapped_asset_keys_by_dag_id["daily_dag"] == {
        AssetKey("double_targeted_asset"),
    }

    assert mapping_info.task_handle_map[AssetKey("other_asset")] == {
        TaskHandle(dag_id="weekly_dag", task_id="task1")
    }
    assert mapping_info.task_handle_map[AssetKey("double_targeted_asset")] == {
        TaskHandle(dag_id="weekly_dag", task_id="task1"),
        TaskHandle(dag_id="daily_dag", task_id="task1"),
    }


def test_double_instance() -> None:
    airflow_instance_one = make_instance(
        dag_and_task_structure={"dag1": ["task1"]},
        instance_name="instance_one",
    )

    airflow_instance_two = make_instance(
        dag_and_task_structure={"dag1": ["task1"]},
        instance_name="instance_two",
    )

    defs_one = build_defs_from_airflow_instance(airflow_instance=airflow_instance_one)
    defs_two = build_defs_from_airflow_instance(airflow_instance=airflow_instance_two)

    defs = Definitions.merge(defs_one, defs_two)

    all_specs = {spec.key: spec for spec in defs.get_all_asset_specs()}

    assert set(all_specs.keys()) == {
        make_default_dag_asset_key("instance_one", "dag1"),
        make_default_dag_asset_key("instance_two", "dag1"),
    }


def test_automapped_dag_with_two_tasks() -> None:
    airflow_instance = make_instance(
        dag_and_task_structure={"dag1": ["task1", "task2"]}, task_deps={"task1": ["task2"]}
    )

    full_defs = build_full_automapped_dags_from_airflow_instance(airflow_instance=airflow_instance)

    all_specs = {spec.key: spec for spec in full_defs.get_all_asset_specs()}

    task_one_key = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task1")
    task_two_key = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task2")
    assert task_one_key in all_specs
    assert task_two_key in all_specs

    assert all_specs[task_one_key].deps == []
    assert all_specs[task_two_key].deps == [AssetDep(task_one_key)]


def test_automapped_dag_with_two_tasks_plus_explicit_defs() -> None:
    airflow_instance = make_instance(
        dag_and_task_structure={"dag1": ["task1", "task2"]}, task_deps={"task1": ["task2"]}
    )

    explicit_asset_1 = AssetKey("explicit_asset1")
    full_defs = build_full_automapped_dags_from_airflow_instance(
        airflow_instance=airflow_instance,
        defs=Definitions(
            assets=assets_with_task_mappings(
                dag_id="dag1",
                task_mappings={
                    "task1": [AssetSpec(explicit_asset_1)],
                },
            )
        ),
    )

    all_specs = {spec.key: spec for spec in full_defs.get_all_asset_specs()}
    assert explicit_asset_1 in all_specs

    task_one_key = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task1")
    task_two_key = key_for_automapped_task_asset(airflow_instance.name, "dag1", "task2")
    assert task_one_key in all_specs
    assert task_two_key in all_specs

    assert all_specs[task_one_key].deps == []
    assert all_specs[task_two_key].deps == [AssetDep(task_one_key)]
