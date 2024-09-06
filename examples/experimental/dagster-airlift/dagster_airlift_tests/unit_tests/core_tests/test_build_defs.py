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
    schedule,
    sensor,
)
from dagster._core.definitions.assets import unique_id_from_asset_and_check_keys
from dagster_airlift.core import build_defs_from_airflow_instance, dag_defs, task_defs
from dagster_airlift.test import make_instance

from dagster_airlift_tests.unit_tests.conftest import (
    assert_dependency_structure_in_assets,
    build_definitions_airflow_asset_graph,
    fully_loaded_repo_from_airflow_asset_graph,
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
def dag__task():
    pass


@asset
def a():
    pass


b_spec = AssetSpec(key="b")


@asset_check(asset=a)
def a_check():
    pass


@asset_check(asset=dag__task)
def other_check():
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

    spec = AssetSpec(key="a", metadata={"airlift/dag_id": "dag", "airlift/task_id": "task"})
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
    assert next(iter(assets_def.specs)).metadata["Dag ID"] == "dag"


def test_invalid_dagster_named_tasks_and_dags() -> None:
    """Test that invalid dagster names are converted to valid names."""
    a = AssetKey("a")
    spec = AssetSpec(
        key=a,
        metadata={"airlift/dag_id": "dag-with-hyphens", "airlift/task_id": "task-with-hyphens"},
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
    unique_id = unique_id_from_asset_and_check_keys([a])
    assert assets_def.node_def.name == f"airflow_task_mapped_{unique_id}"

    assert AssetKey(["airflow_instance", "dag", "dag_with_hyphens"]) in repo.assets_defs_by_key
    dag_def = repo.assets_defs_by_key[AssetKey(["airflow_instance", "dag", "dag_with_hyphens"])]
    assert dag_def.node_def.name == "airflow_instance__dag__dag_with_hyphens"


def test_unique_node_names_from_specs() -> None:
    """When multiple new nodes are created from a single task, ensure that asset dependencies line up.
    Non-unique name issues manifest as input-output connection issues deep in the stack, so by loading
    the cacheable assets, we can check to make sure that inputs/outputs are properly hooked up.
    """
    abc = AssetKey(["a", "b", "c"])
    defg = AssetKey(["d", "e", "f", "g"])
    defs = build_defs_from_airflow_instance(
        airflow_instance=make_instance({"somedag": ["sometask"]}),
        defs=dag_defs(
            "somedag",
            task_defs(
                "sometask",
                defs=Definitions(
                    assets=[AssetSpec(key=abc), AssetSpec(key=defg)],
                ),
            ),
        ),
    )

    repo = defs.get_repository_def()
    repo.load_all_definitions()
    expected_dag_key = AssetKey(["airflow_instance", "dag", "somedag"])
    assert set(repo.assets_defs_by_key.keys()) == {abc, defg, expected_dag_key}
    abc_def = repo.assets_defs_by_key[abc]
    assert (
        abc_def.node_def.name == f"airflow_task_mapped_{unique_id_from_asset_and_check_keys([abc])}"
    )
    defg_def = repo.assets_defs_by_key[defg]
    assert (
        defg_def.node_def.name
        == f"airflow_task_mapped_{unique_id_from_asset_and_check_keys([defg])}"
    )


def test_transitive_asset_deps() -> None:
    """Test that cross-dag transitive asset dependencies rae correctly generated."""
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
    assert "airlift/dag_id" in next(iter(a_asset.specs)).metadata
    assert next(iter(a_asset.specs)).metadata["airlift/dag_id"] == "dag1"
    assert "airlift/task_id" in next(iter(a_asset.specs)).metadata
    assert next(iter(a_asset.specs)).metadata["airlift/task_id"] == "task"

    b_asset = repo_def.assets_defs_by_key[b_key]
    assert [dep.asset_key for dep in next(iter(b_asset.specs)).deps] == [a_key]
    assert "airlift/dag_id" not in next(iter(b_asset.specs)).metadata
    assert "airlift/task_id" not in next(iter(b_asset.specs)).metadata
    c_asset = repo_def.assets_defs_by_key[c_key]
    assert [dep.asset_key for dep in next(iter(c_asset.specs)).deps] == [b_key]
    assert "airlift/dag_id" in next(iter(c_asset.specs)).metadata
    assert next(iter(c_asset.specs)).metadata["airlift/dag_id"] == "dag2"
    assert "airlift/task_id" in next(iter(c_asset.specs)).metadata
    assert next(iter(c_asset.specs)).metadata["airlift/task_id"] == "task"


def test_peered_dags() -> None:
    """Test peered dags show up, and that linkage is preserved downstream of dags."""
    defs = build_definitions_airflow_asset_graph(
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
    # Assets are not loaded until repository is loaded
    assert len(list(defs.assets)) == 1
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
    defs = build_definitions_airflow_asset_graph(
        assets_per_task={
            "dag": {
                "task1": [("a", []), ("b", ["a"]), ("c", ["a"])],
                "task2": [("d", ["b", "c"]), ("e", ["d"]), ("f", ["d"])],
            },
        },
    )
    assert defs.assets
    assert len(list(defs.assets)) == 1
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
