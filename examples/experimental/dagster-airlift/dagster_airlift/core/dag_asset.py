from typing import Any, Dict, List, Mapping, Sequence, Set

from dagster import AssetKey, JsonMetadataValue, MarkdownMetadataValue
from dagster._core.definitions.metadata.metadata_value import UrlMetadataValue

from dagster_airlift.constants import STANDALONE_DAG_ID_METADATA_KEY
from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo
from dagster_airlift.core.serialization.serialized_data import (
    SerializedAssetDepData,
    SerializedAssetSpecData,
)
from dagster_airlift.core.utils import airflow_kind_dict


def dag_asset_spec_data(
    airflow_instance: AirflowInstance,
    asset_keys_for_leaf_tasks: Sequence[AssetKey],
    dag_info: DagInfo,
) -> SerializedAssetSpecData:
    return SerializedAssetSpecData(
        asset_key=dag_info.dag_asset_key,
        description=dag_description(dag_info),
        metadata=dag_asset_metadata(airflow_instance, dag_info),
        tags=airflow_kind_dict(),
        deps=[
            SerializedAssetDepData(asset_key=leaf_asset_key)
            for leaf_asset_key in asset_keys_for_leaf_tasks
        ],
    )


def dag_description(dag_info: DagInfo) -> str:
    return f"""
    A materialization corresponds to a successful run of airflow DAG {dag_info.dag_id}.
    """


def dag_asset_metadata(airflow_instance: AirflowInstance, dag_info: DagInfo) -> Mapping[str, Any]:
    metadata = {
        "Dag Info (raw)": JsonMetadataValue(dag_info.metadata),
        "Dag ID": dag_info.dag_id,
        "Link to DAG": UrlMetadataValue(dag_info.url),
        STANDALONE_DAG_ID_METADATA_KEY: dag_info.dag_id,
    }
    source_code = airflow_instance.get_dag_source_code(dag_info.metadata["file_token"])
    # Attempt to retrieve source code from the DAG.
    metadata["Source Code"] = MarkdownMetadataValue(
        f"""
```python
{source_code}
```
            """
    )
    return metadata


def get_leaf_assets_for_dag(
    asset_keys_in_dag: Set[AssetKey],
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
) -> List[AssetKey]:
    # An asset is a "leaf" for the dag if it has no transitive dependencies _within_ the dag. It may have
    # dependencies _outside_ the dag.
    leaf_assets = []
    cache = {}
    for asset_key in asset_keys_in_dag:
        if (
            get_transitive_dependencies_for_asset(
                asset_key, downstreams_asset_dependency_graph, cache
            ).intersection(asset_keys_in_dag)
            == set()
        ):
            leaf_assets.append(asset_key)
    return leaf_assets


def get_transitive_dependencies_for_asset(
    asset_key: AssetKey,
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
    cache: Dict[AssetKey, Set[AssetKey]],
) -> Set[AssetKey]:
    if asset_key in cache:
        return cache[asset_key]
    transitive_deps = set()
    for dep in downstreams_asset_dependency_graph[asset_key]:
        transitive_deps.add(dep)
        transitive_deps.update(
            get_transitive_dependencies_for_asset(dep, downstreams_asset_dependency_graph, cache)
        )
    cache[asset_key] = transitive_deps
    return transitive_deps
