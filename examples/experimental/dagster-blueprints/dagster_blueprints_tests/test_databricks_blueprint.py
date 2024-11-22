from typing import Dict, cast
from unittest.mock import MagicMock

from dagster import (
    AssetKey,
    AssetsDefinition,
    Definitions,
    MaterializeResult,
    PipesClient,
    materialize,
)
from dagster._core.pipes.client import PipesClientCompletedInvocation
from dagster_blueprints.blueprint_assets_definition import AssetSpecModel
from dagster_blueprints.databricks_blueprint import DatabricksTaskBlueprint
from databricks.sdk.service import jobs

CLUSTER_DEFAULTS = {
    "spark_version": "12.2.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 0,
}

TASK_KEY = "DAGSTER_PIPES_TASK"


def make_submit_task_dict(
    script_path: str, dagster_pipes_whl_path: str, forward_logs: bool
) -> dict[str, object]:
    cluster_settings = CLUSTER_DEFAULTS.copy()
    if forward_logs:
        cluster_settings["cluster_log_conf"] = {
            "dbfs": {"destination": "dbfs:/cluster-logs"},
        }
    return {
        "new_cluster": cluster_settings,
        "libraries": [
            {"whl": dagster_pipes_whl_path},
        ],
        "task_key": TASK_KEY,
        "spark_python_task": {
            "python_file": f"dbfs:{script_path}",
            "source": jobs.Source.WORKSPACE,
        },
    }


class MockDatabricksClient(PipesClient):
    def __init__(self, results, expected_databricks_task):
        self.results = results
        self.expected_databricks_task = expected_databricks_task

    def run(self, *, context, extras=None, **kwargs) -> PipesClientCompletedInvocation:
        assert self.expected_databricks_task == kwargs["task"]
        return MagicMock(get_results=lambda: self.results)


def test_single_databricks_task_blueprint() -> None:
    databricks_task_dict = make_submit_task_dict("/my/script/path.py", "/my/whl/path.whl", True)
    single_asset_blueprint = DatabricksTaskBlueprint(
        assets=[AssetSpecModel(key="asset1")], task=databricks_task_dict
    )
    defs = single_asset_blueprint.build_defs()
    asset1 = cast(AssetsDefinition, next(iter(defs.assets or [])))
    assert asset1.key == AssetKey("asset1")
    assert materialize(
        [asset1],
        resources={
            "pipes_databricks_client": MockDatabricksClient(
                results=None,
                expected_databricks_task=jobs.SubmitTask.from_dict(databricks_task_dict),
            )
        },
    ).success


def test_single_databricks_task_blueprint_with_result() -> None:
    databricks_task_dict = make_submit_task_dict("/my/script/path.py", "/my/whl/path.whl", True)
    single_asset_blueprint = DatabricksTaskBlueprint(
        assets=[AssetSpecModel(key="asset1")], task=databricks_task_dict
    )
    defs = single_asset_blueprint.build_defs()
    asset1 = cast(AssetsDefinition, next(iter(defs.assets or [])))
    assert asset1.key == AssetKey("asset1")
    result = materialize(
        [asset1],
        resources={
            "pipes_databricks_client": MockDatabricksClient(
                results=MaterializeResult(metadata={"foo": "bar"}),
                expected_databricks_task=jobs.SubmitTask.from_dict(databricks_task_dict),
            )
        },
    )
    assert result.success
    mat = result.get_asset_materialization_events()[0].step_materialization_data.materialization
    assert mat.metadata["foo"].value == "bar"


def test_multi_asset_databricks_task_blueprint() -> None:
    databricks_task_dict = make_submit_task_dict("/my/script/path.py", "/my/whl/path.whl", True)
    multi_asset_blueprint = DatabricksTaskBlueprint(
        assets=[AssetSpecModel(key="asset1"), AssetSpecModel(key="asset2")],
        task=databricks_task_dict,
    )
    defs = multi_asset_blueprint.build_defs()
    assets = cast(AssetsDefinition, next(iter(defs.assets or [])))
    assert assets.keys == {AssetKey("asset1"), AssetKey("asset2")}
    assert materialize(
        [assets],
        resources={
            "pipes_databricks_client": MockDatabricksClient(
                results=None,
                expected_databricks_task=jobs.SubmitTask.from_dict(databricks_task_dict),
            )
        },
    ).success


def test_multi_asset_databricks_task_blueprint_with_results() -> None:
    databricks_task_dict = make_submit_task_dict("/my/script/path.py", "/my/whl/path.whl", True)
    multi_asset_blueprint = DatabricksTaskBlueprint(
        assets=[AssetSpecModel(key="asset1"), AssetSpecModel(key="asset2")],
        task=databricks_task_dict,
    )
    defs = multi_asset_blueprint.build_defs()
    assets = cast(AssetsDefinition, next(iter(defs.assets or [])))
    assert assets.keys == {AssetKey("asset1"), AssetKey("asset2")}
    result = materialize(
        [assets],
        resources={
            "pipes_databricks_client": MockDatabricksClient(
                results=(
                    MaterializeResult(asset_key="asset1", metadata={"foo": "bar"}),
                    MaterializeResult(asset_key="asset2", metadata={"baz": "qux"}),
                ),
                expected_databricks_task=jobs.SubmitTask.from_dict(databricks_task_dict),
            )
        },
    )
    assert result.success

    mat1 = result.get_asset_materialization_events()[0].step_materialization_data.materialization
    mat2 = result.get_asset_materialization_events()[1].step_materialization_data.materialization

    assert mat1.asset_key == AssetKey("asset1")
    assert mat1.metadata["foo"].value == "bar"
    assert mat2.asset_key == AssetKey("asset2")
    assert mat2.metadata["baz"].value == "qux"


def test_op_name_collisions() -> None:
    single_asset_blueprint1 = DatabricksTaskBlueprint(
        assets=[AssetSpecModel(key="asset1")], task={"placeholder": "placeholder"}
    )
    single_asset_blueprint2 = DatabricksTaskBlueprint(
        assets=[AssetSpecModel(key="asset2")], task={"placeholder": "placeholder"}
    )
    resources = {"pipes_databricks_client": object()}
    blueprint_defs = Definitions.merge(
        single_asset_blueprint1.build_defs(),
        single_asset_blueprint2.build_defs(),
        Definitions(resources=resources),
    )
    Definitions.validate_loadable(blueprint_defs)
