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
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import AssetKey, Output
from dagster._core.definitions.logical_version import CODE_VERSION_TAG_KEY, INPUT_EVENT_POINTER_TAG_KEY_PREFIX, INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX, LOGICAL_VERSION_TAG_KEY
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult


class MockIOManager(IOManager):
    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        pass


@io_manager
def mock_io_manager():
    return MockIOManager()


def get_mat_from_sequence(
    key: AssetKey, sequence: Sequence[AssetMaterialization]
) -> AssetMaterialization:
    for output in sequence:
        if output.asset_key == key:
            return output
    assert False


def get_mat_from_result(
    result: ExecuteInProcessResult, node_str: str
) -> AssetMaterialization:
    mats = result.asset_materializations_for_node(node_str)
    assert len(mats) == 1
    assert isinstance(mats[0], AssetMaterialization)
    return mats[0]

def get_upstream_version_from_mat_provenance(mat: AssetMaterialization, upstream_asset_key: AssetKey) -> str:
    assert mat.tags
    return mat.tags[f"{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/{upstream_asset_key.to_user_string()}"]

def get_version_from_mat(mat: AssetMaterialization) -> str:
    assert mat.tags
    return mat.tags[LOGICAL_VERSION_TAG_KEY]


def assert_same_versions(
    mat1: AssetMaterialization, mat2: AssetMaterialization, code_version: str
) -> None:
    assert mat1.tags
    assert mat1.tags[CODE_VERSION_TAG_KEY] == code_version
    assert mat1.tags[LOGICAL_VERSION_TAG_KEY] is not None
    assert mat2.tags
    assert mat2.tags[CODE_VERSION_TAG_KEY] == code_version
    assert mat2.tags[LOGICAL_VERSION_TAG_KEY] == mat1.tags["dagster/logical_version"]


def assert_different_versions(mat1: AssetMaterialization, mat2: AssetMaterialization) -> None:
    assert mat1.tags
    assert mat1.tags[CODE_VERSION_TAG_KEY] is not None
    assert mat1.tags[LOGICAL_VERSION_TAG_KEY] is not None
    assert mat2.tags
    assert mat2.tags[LOGICAL_VERSION_TAG_KEY] != mat1.tags["dagster/logical_version"]

def assert_provenance_match(mat: AssetMaterialization, upstream_mat: AssetMaterialization) -> None:
    mat_prov_lv = get_upstream_version_from_mat_provenance(mat, upstream_mat.asset_key)
    upstream_mat_lv = get_version_from_mat(upstream_mat)
    assert mat_prov_lv == upstream_mat_lv

# Check that mat references upstream mat in its provenance
def assert_provenance_no_match(mat: AssetMaterialization, upstream_mat: AssetMaterialization) -> None:
    mat_prov_lv = get_upstream_version_from_mat_provenance(mat, upstream_mat.asset_key)
    upstream_mat_lv = get_version_from_mat(upstream_mat)
    assert mat_prov_lv != upstream_mat_lv

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
    mat = get_mat_from_result(result, node_str)

    assert isinstance(mat, AssetMaterialization)
    return mat


def materialize_assets(
    assets: Sequence[AssetsDefinition], instance: DagsterInstance
) -> Iterable[AssetMaterialization]:
    result = materialize(assets, instance=instance, resources={"io_manager": mock_io_manager})
    for asset_def in assets:
        node_str = asset_def.node_def.name if asset_def.node_def else asset_def.key.path[-1]
        for mat in result.asset_materializations_for_node(node_str):
            yield cast(AssetMaterialization, mat)


def materialize_twice(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
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


# def test_multi_asset():
#     @asset
#     def start():
#         return 1
#
#     @multi_asset(
#         outs={
#             "a": AssetOut(is_required=False),
#             "b": AssetOut(is_required=False),
#             "c": AssetOut(is_required=False),
#         },
#         internal_asset_deps={
#             "a": {AssetKey("start")},
#             "b": {AssetKey("a")},
#             "c": {AssetKey("a")},
#         },
#         can_subset=True,
#     )
#     def abc_(context, start):
#         a = (start + 1) if start else 1
#         b = a + 1
#         c = a + 2
#         out_values = {"a": a, "b": b, "c": c}
#         outputs_to_return = context.selected_output_names
#         for output_name in outputs_to_return:
#             yield Output(out_values[output_name], output_name)
#
#     instance = DagsterInstance.ephemeral()
#     mats_1 = list(materialize_assets([start, abc_], instance))
#     mat_a_1 = get_mat_from_sequence(AssetKey("a"), mats_1)
#     mats_2 = list(materialize_assets([start, abc_], instance))
#     mat_b_2 = get_mat_from_sequence(AssetKey("a"), mats_2)
#     from IPython import embed; embed()
#     assert_provenance_no_match(mat_b_2, mat_a_1)
#
#
