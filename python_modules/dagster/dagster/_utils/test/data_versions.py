from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union, cast, overload

from typing_extensions import Literal

from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import (
    CODE_VERSION_TAG,
    DATA_VERSION_TAG,
    INPUT_DATA_VERSION_TAG_PREFIX,
    CachingStaleStatusResolver,
    DataVersion,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.run_config import RunConfig
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.storage.io_manager import IOManager, io_manager


class MaterializationTable:
    def __init__(self, materializations: Mapping[AssetKey, AssetMaterialization]):
        self.materializations = materializations

    def __getitem__(self, key: Union[str, AssetKey]) -> AssetMaterialization:
        asset_key = AssetKey([key]) if isinstance(key, str) else key
        return self.materializations[asset_key]


# Used to provide source asset dependency
class MockIOManager(IOManager):
    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        return 1


@io_manager
def mock_io_manager():
    return MockIOManager()


def get_mat_from_result(result: ExecuteInProcessResult, node_str: str) -> AssetMaterialization:
    mats = result.asset_materializations_for_node(node_str)
    assert all(isinstance(m, AssetMaterialization) for m in mats)
    return cast(AssetMaterialization, mats[0])


def get_mats_from_result(
    result: ExecuteInProcessResult, assets: Sequence[AssetsDefinition]
) -> MaterializationTable:
    mats: Dict[AssetKey, AssetMaterialization] = {}
    for asset_def in assets:
        node_str = asset_def.node_def.name if asset_def.node_def else asset_def.key.path[-1]
        for mat in result.asset_materializations_for_node(node_str):
            mats[mat.asset_key] = cast(AssetMaterialization, mat)
    return MaterializationTable(mats)


def get_upstream_version_from_mat_provenance(
    mat: AssetMaterialization, upstream_asset_key: AssetKey
) -> str:
    assert mat.tags
    return mat.tags[f"{INPUT_DATA_VERSION_TAG_PREFIX}/{upstream_asset_key.to_user_string()}"]


def get_version_from_mat(mat: AssetMaterialization) -> str:
    assert mat.tags
    return mat.tags[DATA_VERSION_TAG]


def assert_data_version(mat: AssetMaterialization, version: Union[str, DataVersion]) -> None:
    value = version.value if isinstance(version, DataVersion) else version
    assert mat.tags
    assert mat.tags[DATA_VERSION_TAG] == value


def assert_code_version(mat: AssetMaterialization, version: str) -> None:
    assert mat.tags
    assert mat.tags[CODE_VERSION_TAG] == version


def assert_same_versions(
    mat1: AssetMaterialization, mat2: AssetMaterialization, code_version: str
) -> None:
    assert mat1.tags
    assert mat1.tags[CODE_VERSION_TAG] == code_version
    assert mat1.tags[DATA_VERSION_TAG] is not None
    assert mat2.tags
    assert mat2.tags[CODE_VERSION_TAG] == code_version
    assert mat2.tags[DATA_VERSION_TAG] == mat1.tags[DATA_VERSION_TAG]


def assert_different_versions(mat1: AssetMaterialization, mat2: AssetMaterialization) -> None:
    assert mat1.tags
    assert mat1.tags[CODE_VERSION_TAG] is not None
    assert mat1.tags[DATA_VERSION_TAG] is not None
    assert mat2.tags
    assert mat2.tags[DATA_VERSION_TAG] != mat1.tags[DATA_VERSION_TAG]


def assert_provenance_match(mat: AssetMaterialization, upstream_mat: AssetMaterialization) -> None:
    mat_prov_dv = get_upstream_version_from_mat_provenance(mat, upstream_mat.asset_key)
    upstream_mat_dv = get_version_from_mat(upstream_mat)
    assert mat_prov_dv == upstream_mat_dv


# Check that mat references upstream mat in its provenance
def assert_provenance_no_match(
    mat: AssetMaterialization, upstream_mat: AssetMaterialization
) -> None:
    mat_prov_dv = get_upstream_version_from_mat_provenance(mat, upstream_mat.asset_key)
    upstream_mat_dv = get_version_from_mat(upstream_mat)
    assert mat_prov_dv != upstream_mat_dv


@overload
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    *,
    is_multi: Literal[True],
    partition_key: Optional[str] = ...,
    run_config: Optional[Union[RunConfig, Mapping[str, Any]]] = ...,
    tags: Optional[Mapping[str, str]] = ...,
) -> MaterializationTable: ...


@overload
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    *,
    is_multi: Literal[False] = ...,
    partition_key: Optional[str] = ...,
    run_config: Optional[Union[RunConfig, Mapping[str, Any]]] = ...,
    tags: Optional[Mapping[str, str]] = ...,
) -> AssetMaterialization: ...


# Use only for AssetsDefinition with one asset
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    *,
    is_multi: bool = False,
    partition_key: Optional[str] = None,
    run_config: Optional[Union[RunConfig, Mapping[str, Any]]] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> Union[AssetMaterialization, MaterializationTable]:
    assets: List[Union[AssetsDefinition, SourceAsset]] = []
    for asset_def in all_assets:
        if isinstance(asset_def, SourceAsset):
            assets.append(asset_def)
        else:
            assert isinstance(asset_def, AssetsDefinition)
            if asset_def == asset_to_materialize:
                assets.append(asset_def)
            else:
                assets.append(asset_def.to_source_assets()[0])

    result = materialize(
        assets,
        instance=instance,
        resources={"io_manager": mock_io_manager},
        partition_key=partition_key,
        run_config=run_config,
        tags=tags,
    )
    if is_multi:
        return get_mats_from_result(result, [asset_to_materialize])
    else:
        node_str = asset_to_materialize.key.path[-1]
        return get_mat_from_result(result, node_str)


def materialize_assets(
    assets: Sequence[AssetsDefinition],
    instance: DagsterInstance,
    partition_key: Optional[str] = None,
    run_config: Optional[Mapping[str, Any]] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> MaterializationTable:
    result = materialize(
        assets,
        instance=instance,
        resources={"io_manager": mock_io_manager},
        partition_key=partition_key,
        run_config=run_config,
        tags=tags,
    )
    return get_mats_from_result(result, assets)


def materialize_twice(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
) -> Tuple[AssetMaterialization, AssetMaterialization]:
    mat1 = materialize_asset(all_assets, asset_to_materialize, instance)
    mat2 = materialize_asset(all_assets, asset_to_materialize, instance)
    return mat1, mat2


def get_stale_status_resolver(
    instance: DagsterInstance,
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
) -> CachingStaleStatusResolver:
    return CachingStaleStatusResolver(
        instance=instance,
        asset_graph=AssetGraph.from_assets(assets),
    )
