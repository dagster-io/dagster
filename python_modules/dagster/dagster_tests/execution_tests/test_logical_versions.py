# pylint: disable=unused-argument

from typing import Iterable, List, Sequence, Tuple, Union, cast

from dagster import (
    AssetMaterialization,
    AssetsDefinition,
    DagsterInstance,
    IOManager,
    SourceAsset,
    asset,
    io_manager,
    materialize,
)
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult


class MockIOManager(IOManager):
    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        pass


@io_manager
def mock_io_manager():
    return MockIOManager()


def get_materialization_from_result(
    result: ExecuteInProcessResult, node_str: str
) -> AssetMaterialization:
    mats = result.asset_materializations_for_node(node_str)
    assert len(mats) == 1
    assert isinstance(mats[0], AssetMaterialization)
    return mats[0]


def assert_same_versions(
    mat1: AssetMaterialization, mat2: AssetMaterialization, code_version: str
) -> None:
    assert mat1.tags
    assert mat1.tags["dagster/code_version"] == code_version
    assert mat1.tags["dagster/logical_version"] is not None
    assert mat2.tags
    assert mat2.tags["dagster/code_version"] == code_version
    assert mat2.tags["dagster/logical_version"] == mat1.tags["dagster/logical_version"]


def assert_different_versions(mat1: AssetMaterialization, mat2: AssetMaterialization) -> None:
    assert mat1.tags
    assert mat1.tags["dagster/code_version"] is not None
    assert mat1.tags["dagster/logical_version"] is not None
    assert mat2.tags
    assert mat2.tags["dagster/logical_version"] != mat1.tags["dagster/logical_version"]


def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
) -> AssetMaterialization:
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

    result = materialize(assets, instance=instance, resources={"io_manager": mock_io_manager})
    node_str = asset_to_materialize.key.path[-1]
    mat = get_materialization_from_result(result, node_str)

    assert isinstance(mat, AssetMaterialization)
    return mat


def materialize_assets(assets, instance) -> Iterable[AssetMaterialization]:
    result = materialize(assets, instance=instance, resources={"io_manager": mock_io_manager})
    for asset_def in assets:
        if isinstance(asset_def, AssetsDefinition):
            node_str = asset_def.key.path[-1]
            yield cast(AssetMaterialization, get_materialization_from_result(result, node_str))


def materialize_twice(
    all_assets, asset_to_materialize, instance
) -> Tuple[AssetMaterialization, AssetMaterialization]:
    mat1 = materialize_asset(all_assets, asset_to_materialize, instance)
    mat2 = materialize_asset(all_assets, asset_to_materialize, instance)
    return mat1, mat2


def test_single_asset():
    @asset
    def asset1():
        ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_single_versioned_asset():
    @asset(op_version="abc")
    def asset1():
        ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([asset1], asset1, instance)
    assert_same_versions(mat1, mat2, "abc")


def test_source_asset_non_versioned_asset():
    source1 = SourceAsset("source1")

    @asset
    def asset1(source1):
        ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([source1, asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_source_asset_versioned_asset():
    source1 = SourceAsset("source1")

    @asset(op_version="abc")
    def asset1(source1):
        ...

    instance = DagsterInstance.ephemeral()

    mat1, mat2 = materialize_twice([source1, asset1], asset1, instance)
    assert_same_versions(mat1, mat2, "abc")


def test_source_asset_non_versioned_asset_non_argument_deps():
    source1 = SourceAsset("source1")

    @asset(non_argument_deps={"source1"})
    def asset1():
        ...

    instance = DagsterInstance.ephemeral()

    mat1, mat2 = materialize_twice([source1, asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_versioned_after_unversioned():
    source1 = SourceAsset("source1")

    @asset
    def asset1(source1):
        ...

    @asset(op_version="abc")
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    instance = DagsterInstance.ephemeral()

    _, asset2_mat1 = materialize_assets(all_assets, instance)
    asset2_mat2 = materialize_asset(all_assets, asset2, instance)
    assert_same_versions(asset2_mat1, asset2_mat2, "abc")

    materialize_asset(all_assets, asset1, instance)

    asset2_mat3 = materialize_asset(all_assets, asset2, instance)
    assert_different_versions(asset2_mat2, asset2_mat3)


def test_versioned_after_versioned():
    source1 = SourceAsset("source1")

    @asset(op_version="abc")
    def asset1(source1):
        ...

    @asset(op_version="xyz")
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    instance = DagsterInstance.ephemeral()

    _, asset2_mat1 = materialize_assets(all_assets, instance)
    _, asset2_mat2 = materialize_assets(all_assets, instance)
    asset2_mat3 = materialize_asset(all_assets, asset2, instance)

    assert_same_versions(asset2_mat1, asset2_mat2, "xyz")
    assert_same_versions(asset2_mat1, asset2_mat3, "xyz")


def test_unversioned_after_versioned():
    source1 = SourceAsset("source1")

    @asset(op_version="abc")
    def asset1(source1):
        ...

    @asset
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    instance = DagsterInstance.ephemeral()

    _, asset2_mat1 = materialize_assets(all_assets, instance)
    asset2_mat2 = materialize_asset(all_assets, asset2, instance)

    assert_different_versions(asset2_mat1, asset2_mat2)
