from pathlib import Path
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
from dagster._core.test_utils import environ
from dagster._serdes.serdes import deserialize_value
from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core import (
    build_defs_from_airflow_instance as build_defs_from_airflow_instance,
)
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.serialization.compute import compute_serialized_data, is_mapped_asset_spec
from dagster_airlift.core.state_backed_defs_loader import (
    scoped_reconstruction_metadata,
    unwrap_reconstruction_metadata,
)
from dagster_airlift.core.utils import metadata_for_task_mapping
from dagster_airlift.test import make_instance
from dagster_airlift.utils import DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR

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
        AssetKey(["airflow_instance", "dag", "dag"]),
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
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance({"dag-with-hyphens": ["task-with-hyphens"]}),
        defs=Definitions(
            assets=[spec],
        ),
    )

    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) == 2
    assert a in repo.assets_defs_by_key
    assets_def = repo.assets_defs_by_key[a]
    assert not assets_def.is_executable

    assert AssetKey(["airflow_instance", "dag", "dag_with_hyphens"]) in repo.assets_defs_by_key
    dag_def = repo.assets_defs_by_key[AssetKey(["airflow_instance", "dag", "dag_with_hyphens"])]
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
    dag1_key = AssetKey(["airflow_instance", "dag", "dag1"])
    dag2_key = AssetKey(["airflow_instance", "dag", "dag2"])
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
    assert not is_mapped_asset_spec(next(iter(b_asset.specs)))

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
            assets=[
                AssetSpec(key="a", deps=[AssetKey.from_user_string("airflow_instance/dag/dag1")])
            ]
        ),
    )
    assert defs.assets
    repo_def = defs.get_repository_def()
    repo_def.load_all_definitions()
    assert len(repo_def.assets_defs_by_key) == 4
    assert_dependency_structure_in_assets(
        repo_def=repo_def,
        expected_deps={
            "airflow_instance/dag/dag1": [],
            "airflow_instance/dag/dag2": [],
            "airflow_instance/dag/dag3": [],
            "a": ["airflow_instance/dag/dag1"],
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
            "airflow_instance/dag/dag": ["e", "f"],
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

    with environ(
        {
            DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR: str(
                Path(__file__).parent / "migration_state_for_sqlite_test"
            ),
        }
    ):
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
    } == {a, AssetKey(["airflow_instance", "dag", "dag"])}
    assert len(defs.metadata) == 1
    assert "dagster-airlift/source/test_instance" in defs.metadata
    assert isinstance(defs.metadata["dagster-airlift/source/test_instance"].value, str)
    assert isinstance(
        deserialize_value(defs.metadata["dagster-airlift/source/test_instance"].value),
        AirflowDefinitionsData,
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
            } == {a, AssetKey(["airflow_instance", "dag", "dag"])}
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
        AssetKey(["airflow_instance", "dag", "dag1"]),
        AssetKey(["airflow_instance", "dag", "dag2"]),
    }
    repo_def = defs.get_repository_def()
    a_and_b_asset = repo_def.assets_defs_by_key[AssetKey("a")]
    a_spec = next(iter(spec for spec in a_and_b_asset.specs if spec.key == AssetKey("a")))
    assert has_single_task_handle(a_spec, "dag1", "task1")
    b_spec = next(iter(spec for spec in a_and_b_asset.specs if spec.key == AssetKey("b")))
    assert has_single_task_handle(b_spec, "dag2", "task2")
