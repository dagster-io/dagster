from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Sequence, Tuple, Union

from dagster import (
    AssetKey,
    AssetObservation,
    AssetSpec,
    Definitions,
    SensorEvaluationContext,
    SensorResult,
    SourceAsset,
    build_sensor_context,
    multi_asset,
)
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._time import get_current_datetime
from dagster_airlift.core import DagDefs, build_defs_from_airflow_instance, dag_defs, task_defs
from dagster_airlift.test import make_dag_run, make_instance

if TYPE_CHECKING:
    from dagster_airlift.core.dag_defs import DagDefs


def strip_to_first_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def fully_loaded_repo_from_airflow_asset_graph(
    assets_per_task: Dict[str, Dict[str, List[Tuple[str, List[str]]]]],
    additional_defs: Definitions = Definitions(),
    create_runs: bool = True,
) -> RepositoryDefinition:
    defs = build_definitions_airflow_asset_graph(
        assets_per_task, additional_defs=additional_defs, create_runs=create_runs
    )
    repo_def = defs.get_repository_def()
    repo_def.load_all_definitions()
    return repo_def


def build_definitions_airflow_asset_graph(
    assets_per_task: Dict[str, Dict[str, List[Tuple[str, List[str]]]]],
    additional_defs: Definitions = Definitions(),
    create_runs: bool = True,
    create_assets_defs: bool = True,
) -> Definitions:
    dag_defs_list: List[Union[Definitions, "DagDefs"]] = [additional_defs]
    dag_and_task_structure = defaultdict(list)
    for dag_id, task_structure in assets_per_task.items():
        task_defs_list = []
        for task_id, asset_structure in task_structure.items():
            dag_and_task_structure[dag_id].append(task_id)
            assets = []
            for asset_key, deps in asset_structure:
                spec = AssetSpec(
                    asset_key,
                    deps=deps,
                    metadata={"airlift/dag_id": dag_id, "airlift/task_id": task_id},
                )
                if create_assets_defs:

                    @multi_asset(specs=[spec], name=f"{task_id}_{asset_key}")
                    def _asset():
                        return None

                    assets.append(_asset)
                else:
                    assets.append(spec)
            task_defs_list.append(task_defs(task_id, Definitions(assets=assets)))
        dag_defs_list.append(dag_defs(dag_id, task_defs_list))
    runs = (
        [
            make_dag_run(
                dag_id=dag_id,
                run_id=f"run-{dag_id}",
                start_date=get_current_datetime() - timedelta(minutes=10),
                end_date=get_current_datetime(),
            )
            for dag_id in dag_and_task_structure.keys()
        ]
        if create_runs
        else []
    )
    instance = make_instance(
        dag_and_task_structure=dag_and_task_structure,
        dag_runs=runs,
    )
    return build_defs_from_airflow_instance(instance, dag_defs_list=dag_defs_list)


def build_and_invoke_sensor(
    assets_per_task: Dict[str, Dict[str, List[Tuple[str, List[str]]]]],
    additional_defs: Definitions = Definitions(),
) -> Tuple[SensorResult, SensorEvaluationContext]:
    repo_def = fully_loaded_repo_from_airflow_asset_graph(
        assets_per_task, additional_defs=additional_defs
    )
    sensor = next(iter(repo_def.sensor_defs))
    context = build_sensor_context(repository_def=repo_def)
    result = sensor(context)
    assert isinstance(result, SensorResult)
    return result, context


def assert_expected_key_order(
    mats: Sequence[Union[AssetMaterialization, AssetObservation, AssetCheckEvaluation]],
    expected_key_order: Sequence[str],
) -> None:
    assert all(isinstance(mat, AssetMaterialization) for mat in mats)
    assert [mat.asset_key.to_user_string() for mat in mats] == expected_key_order


def assert_dependency_structure_in_assets(
    repo_def: RepositoryDefinition, expected_deps: Dict[str, List[str]]
) -> None:
    for key, deps_list in expected_deps.items():
        qual_key = AssetKey.from_user_string(key)
        assert qual_key in repo_def.assets_defs_by_key
        assets_def = repo_def.assets_defs_by_key[qual_key]
        spec = next(spec for spec in assets_def.specs if spec.key == qual_key)
        assert {dep.asset_key for dep in spec.deps} == {
            AssetKey.from_user_string(dep) for dep in deps_list
        }


def dag_defs_with_override() -> "DagDefs":
    """A test dag_defs call with an override applied."""

    class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
            return []

        def build_definitions(
            self, data: Sequence[AssetsDefinitionCacheableData]
        ) -> Sequence[AssetsDefinition]:
            @multi_asset(specs=[AssetSpec(key="c", metadata={"airlift/dag_id": "dag_one"})])
            def _asset():
                return None

            return [_asset]

    return dag_defs(
        "dag_one",
        [
            task_defs("task_one", Definitions(assets=[])),
        ],
        override=Definitions(
            assets=[
                AssetSpec(key="a"),
                SourceAsset(key="b"),
                MyCacheableAssetsDefinition(unique_id="c"),
            ]
        ),
    )
