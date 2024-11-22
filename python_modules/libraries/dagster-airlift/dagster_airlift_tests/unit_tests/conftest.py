from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Generator, List, Optional, Sequence, Tuple, Union

import pytest
from dagster import (
    AssetKey,
    AssetObservation,
    AssetSpec,
    DagsterInstance,
    Definitions,
    SensorEvaluationContext,
    SensorResult,
    build_sensor_context,
    multi_asset,
)
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.test_utils import instance_for_test
from dagster._time import get_current_datetime
from dagster_airlift.core import (
    build_defs_from_airflow_instance as build_defs_from_airflow_instance,
)
from dagster_airlift.core.sensor.event_translation import (
    DagsterEventTransformerFn,
    default_event_transformer,
)
from dagster_airlift.core.utils import metadata_for_dag_mapping, metadata_for_task_mapping
from dagster_airlift.test import make_dag_run, make_instance


def strip_to_first_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def fully_loaded_repo_from_airflow_asset_graph(
    assets_per_task: dict[str, dict[str, list[tuple[str, list[str]]]]],
    additional_defs: Definitions = Definitions(),
    create_runs: bool = True,
    dag_level_asset_overrides: Optional[dict[str, list[str]]] = None,
    event_transformer_fn: DagsterEventTransformerFn = default_event_transformer,
) -> RepositoryDefinition:
    defs = load_definitions_airflow_asset_graph(
        assets_per_task,
        additional_defs=additional_defs,
        create_runs=create_runs,
        dag_level_asset_overrides=dag_level_asset_overrides,
        event_transformer_fn=event_transformer_fn,
    )
    repo_def = defs.get_repository_def()
    repo_def.load_all_definitions()
    return repo_def


def load_definitions_airflow_asset_graph(
    assets_per_task: dict[str, dict[str, list[tuple[str, list[str]]]]],
    additional_defs: Definitions = Definitions(),
    create_runs: bool = True,
    create_assets_defs: bool = True,
    dag_level_asset_overrides: Optional[dict[str, list[str]]] = None,
    event_transformer_fn: DagsterEventTransformerFn = default_event_transformer,
) -> Definitions:
    assets = []
    dag_and_task_structure = defaultdict(list)
    for dag_id, task_structure in assets_per_task.items():
        for task_id, asset_structure in task_structure.items():
            dag_and_task_structure[dag_id].append(task_id)
            for asset_key, deps in asset_structure:
                spec = AssetSpec(
                    asset_key,
                    deps=deps,
                    metadata=metadata_for_task_mapping(dag_id=dag_id, task_id=task_id),
                )
                if create_assets_defs:

                    @multi_asset(specs=[spec], name=f"{spec.key.to_python_identifier()}_asset")
                    def _asset():
                        return None

                    assets.append(_asset)
                else:
                    assets.append(spec)
    if dag_level_asset_overrides:
        for dag_id, asset_keys in dag_level_asset_overrides.items():
            dag_and_task_structure[dag_id] = ["dummy_task"]
            for asset in asset_keys:
                spec = AssetSpec(
                    AssetKey.from_user_string(asset),
                    metadata=metadata_for_dag_mapping(dag_id=dag_id),
                )
                if create_assets_defs:

                    @multi_asset(specs=[spec], name=f"{spec.key.to_python_identifier()}_asset")
                    def _asset():
                        return None

                    assets.append(_asset)
                else:
                    assets.append(spec)
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
    defs = Definitions.merge(
        additional_defs,
        Definitions(assets=assets),
    )
    return build_defs_from_airflow_instance(
        airflow_instance=instance, defs=defs, event_transformer_fn=event_transformer_fn
    )


def build_and_invoke_sensor(
    *,
    assets_per_task: dict[str, dict[str, list[tuple[str, list[str]]]]],
    instance: DagsterInstance,
    additional_defs: Definitions = Definitions(),
    dag_level_asset_overrides: Optional[dict[str, list[str]]] = None,
    event_transformer_fn: DagsterEventTransformerFn = default_event_transformer,
) -> tuple[SensorResult, SensorEvaluationContext]:
    repo_def = fully_loaded_repo_from_airflow_asset_graph(
        assets_per_task,
        additional_defs=additional_defs,
        dag_level_asset_overrides=dag_level_asset_overrides,
        event_transformer_fn=event_transformer_fn,
    )
    sensor = next(iter(repo_def.sensor_defs))
    sensor_context = build_sensor_context(repository_def=repo_def, instance=instance)
    result = sensor(sensor_context)
    assert isinstance(result, SensorResult)
    return result, sensor_context


def assert_expected_key_order(
    mats: Sequence[Union[AssetMaterialization, AssetObservation, AssetCheckEvaluation]],
    expected_key_order: Sequence[str],
) -> None:
    assert all(isinstance(mat, AssetMaterialization) for mat in mats)
    assert [mat.asset_key.to_user_string() for mat in mats] == expected_key_order


def assert_dependency_structure_in_assets(
    repo_def: RepositoryDefinition, expected_deps: dict[str, list[str]]
) -> None:
    for key, deps_list in expected_deps.items():
        qual_key = AssetKey.from_user_string(key)
        assert qual_key in repo_def.assets_defs_by_key
        assets_def = repo_def.assets_defs_by_key[qual_key]
        spec = next(spec for spec in assets_def.specs if spec.key == qual_key)
        assert {dep.asset_key for dep in spec.deps} == {
            AssetKey.from_user_string(dep) for dep in deps_list
        }


@pytest.fixture(name="instance")
def instance_fixture() -> Generator[DagsterInstance, None, None]:
    with instance_for_test() as instance:
        yield instance


def _set_init_load_context() -> None:
    """Sets the load context to initialization."""
    DefinitionsLoadContext.set(DefinitionsLoadContext(load_type=DefinitionsLoadType.INITIALIZATION))


@pytest.fixture(name="init_load_context")
def load_context_fixture() -> Generator[None, None, None]:
    """Set initialization load context before and after the test."""
    _set_init_load_context()
    yield
    _set_init_load_context()
