# pylint: disable=unused-argument

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union, cast, overload

from dagster import (
    AssetMaterialization,
    AssetsDefinition,
    DagsterInstance,
    IOManager,
    SourceAsset,
    asset,
    io_manager,
    materialize,
    observable_source_asset,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import AssetKey, Output
from dagster._core.definitions.logical_version import (
    CODE_VERSION_TAG_KEY,
    INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX,
    LOGICAL_VERSION_TAG_KEY,
    CachingStaleStatusResolver,
    LogicalVersion,
    StaleStatus,
    StaleStatusCause,
    compute_logical_version,
)
from dagster._core.definitions.observe import observe
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance_for_test import instance_for_test
from typing_extensions import Literal

# ########################
# ##### HELPERS
# ########################


class MaterializationTable:
    def __init__(self, materializations: Mapping[AssetKey, AssetMaterialization]):
        self.materializations = materializations

    def __getitem__(self, key: Union[str, AssetKey]) -> AssetMaterialization:
        asset_key = AssetKey([key]) if isinstance(key, str) else key
        return self.materializations[asset_key]


# Used to provide sorrce asset dependency
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
    return mat.tags[f"{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/{upstream_asset_key.to_user_string()}"]


def get_version_from_mat(mat: AssetMaterialization) -> str:
    assert mat.tags
    return mat.tags[LOGICAL_VERSION_TAG_KEY]


def assert_logical_version(mat: AssetMaterialization, version: Union[str, LogicalVersion]) -> None:
    value = version.value if isinstance(version, LogicalVersion) else version
    assert mat.tags
    assert mat.tags[LOGICAL_VERSION_TAG_KEY] == value


def assert_code_version(mat: AssetMaterialization, version: str) -> None:
    assert mat.tags
    assert mat.tags[CODE_VERSION_TAG_KEY] == version


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
def assert_provenance_no_match(
    mat: AssetMaterialization, upstream_mat: AssetMaterialization
) -> None:
    mat_prov_lv = get_upstream_version_from_mat_provenance(mat, upstream_mat.asset_key)
    upstream_mat_lv = get_version_from_mat(upstream_mat)
    assert mat_prov_lv != upstream_mat_lv


@overload
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    *,
    is_multi: Literal[True],
) -> MaterializationTable:
    ...


@overload
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    is_multi: Literal[False] = ...,
) -> AssetMaterialization:
    ...


# Use only for AssetsDefinition with one asset
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    is_multi: bool = False,
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

    result = materialize(assets, instance=instance, resources={"io_manager": mock_io_manager})
    if is_multi:
        return get_mats_from_result(result, [asset_to_materialize])
    else:
        node_str = asset_to_materialize.key.path[-1]
        return get_mat_from_result(result, node_str)


def materialize_assets(
    assets: Sequence[AssetsDefinition],
    instance: DagsterInstance,
    run_config: Optional[Dict[str, Any]] = None,
) -> MaterializationTable:
    result = materialize(
        assets,
        instance=instance,
        resources={"io_manager": mock_io_manager},
        run_config=run_config,
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


def get_stale_status_resolver(instance, assets) -> CachingStaleStatusResolver:
    return CachingStaleStatusResolver(
        instance=instance,
        asset_graph=AssetGraph.from_assets(assets),
    )


# ########################
# ##### TESTS
# ########################


def test_single_asset():
    @asset
    def asset1():
        ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_single_versioned_asset():
    @asset(code_version="abc")
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

    @asset(code_version="abc")
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

    @asset(code_version="abc")
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    instance = DagsterInstance.ephemeral()

    asset2_mat1 = materialize_assets(all_assets, instance)[asset2.key]
    asset2_mat2 = materialize_asset(all_assets, asset2, instance)
    assert_same_versions(asset2_mat1, asset2_mat2, "abc")

    materialize_asset(all_assets, asset1, instance)

    asset2_mat3 = materialize_asset(all_assets, asset2, instance)
    assert_different_versions(asset2_mat2, asset2_mat3)


def test_versioned_after_versioned():
    source1 = SourceAsset("source1")

    @asset(code_version="abc")
    def asset1(source1):
        ...

    @asset(code_version="xyz")
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    instance = DagsterInstance.ephemeral()

    asset2_mat1 = materialize_assets(all_assets, instance)[asset2.key]
    asset2_mat2 = materialize_assets(all_assets, instance)[asset2.key]
    asset2_mat3 = materialize_asset(all_assets, asset2, instance)

    assert_same_versions(asset2_mat1, asset2_mat2, "xyz")
    assert_same_versions(asset2_mat1, asset2_mat3, "xyz")


def test_unversioned_after_versioned():
    source1 = SourceAsset("source1")

    @asset(code_version="abc")
    def asset1(source1):
        ...

    @asset
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    instance = DagsterInstance.ephemeral()

    asset2_mat1 = materialize_assets(all_assets, instance)[asset2.key]
    asset2_mat2 = materialize_asset(all_assets, asset2, instance)

    assert_different_versions(asset2_mat1, asset2_mat2)


def test_multi_asset():
    @asset
    def start():
        return 1

    @multi_asset(
        outs={
            "a": AssetOut(is_required=False),
            "b": AssetOut(is_required=False),
            "c": AssetOut(is_required=False),
        },
        internal_asset_deps={
            "a": {AssetKey("start")},
            "b": {AssetKey("a")},
            "c": {AssetKey("a")},
        },
        can_subset=True,
    )
    def abc_(context, start):
        a = (start + 1) if start else 1
        b = a + 1
        c = a + 2
        out_values = {"a": a, "b": b, "c": c}
        outputs_to_return = sorted(context.selected_output_names)
        for output_name in outputs_to_return:
            yield Output(out_values[output_name], output_name)

    instance = DagsterInstance.ephemeral()
    mats_1 = materialize_assets([start, abc_], instance)
    mat_a_1 = mats_1[AssetKey("a")]
    mats_2 = materialize_asset([start, abc_], abc_, instance, is_multi=True)
    mat_a_2 = mats_2[AssetKey("a")]
    mat_b_2 = mats_2[AssetKey("b")]
    assert_provenance_match(mat_b_2, mat_a_2)
    assert_provenance_no_match(mat_b_2, mat_a_1)


def test_multiple_code_versions():
    @multi_asset(
        outs={
            "alpha": AssetOut(code_version="a"),
            "beta": AssetOut(code_version="b"),
        }
    )
    def alpha_beta():
        yield Output(1, "alpha")
        yield Output(2, "beta")

    mats = materialize_assets([alpha_beta], DagsterInstance.ephemeral())
    alpha_mat = mats[AssetKey("alpha")]
    beta_mat = mats[AssetKey("beta")]

    assert_logical_version(alpha_mat, compute_logical_version("a", {}))
    assert_code_version(alpha_mat, "a")
    assert_logical_version(beta_mat, compute_logical_version("b", {}))
    assert_code_version(beta_mat, "b")


def test_stale_status() -> None:
    x = 0

    @observable_source_asset
    def source1(_context):
        nonlocal x
        x = x + 1
        return LogicalVersion(str(x))

    @asset(code_version="abc")
    def asset1(source1):
        ...

    @asset(code_version="xyz")
    def asset2(asset1):
        ...

    # one cause per line for readability

    all_assets = [source1, asset1, asset2]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(source1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_status_causes(asset2.key)[0] == StaleStatusCause(
            StaleStatus.STALE, asset2.key, "never materialized"
        )

        materialize_assets(all_assets, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH

        observe([source1], instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_status_causes(asset1.key) == [
            StaleStatusCause(StaleStatus.STALE, asset1.key, "updated input: source1"),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_status_causes(asset2.key) == [
            StaleStatusCause(StaleStatus.STALE, asset2.key, "stale input: asset1"),
            StaleStatusCause(StaleStatus.STALE, asset1.key, "updated input: source1"),
        ]
        materialize_assets(all_assets, instance)

        # Simulate updating an asset with a new code version
        @asset(name="asset1", code_version="def")
        def asset1_v2(source1):
            ...

        all_assets_v2 = [source1, asset1_v2, asset2]

        status_resolver = get_stale_status_resolver(instance, all_assets_v2)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_status_causes(asset1.key) == [
            StaleStatusCause(StaleStatus.STALE, asset1.key, "updated code version"),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_status_causes(asset2.key) == [
            StaleStatusCause(StaleStatus.STALE, asset2.key, "stale input: asset1"),
            StaleStatusCause(StaleStatus.STALE, asset1.key, "updated code version"),
        ]

        @asset
        def asset3():
            ...

        @asset(name="asset2", code_version="xyz")
        def asset2_v2(asset3):
            ...

        all_assets_v3 = [source1, asset1_v2, asset2_v2, asset3]

        status_resolver = get_stale_status_resolver(instance, all_assets_v3)
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_status_causes(asset2.key) == [
            StaleStatusCause(StaleStatus.STALE, asset2.key, "removed input: asset1"),
            StaleStatusCause(StaleStatus.STALE, asset2.key, "new input: asset3"),
            StaleStatusCause(StaleStatus.STALE, asset3.key, "never materialized"),
        ]


def test_set_logical_version_inside_op():
    instance = DagsterInstance.ephemeral()

    @asset
    def asset1():
        return Output(1, logical_version=LogicalVersion("foo"))

    mat = materialize_asset([asset1], asset1, instance)
    assert_logical_version(mat, LogicalVersion("foo"))


def _get_logical_version_config(**logical_versions: str) -> Dict[str, Any]:
    return {
        "ops": {
            op_name: {"config": {"logical_version": logical_version}}
            for op_name, logical_version in logical_versions.items()
        }
    }


def test_runtime_staleness():
    executed = {
        "alpha": 0,
        "beta": 0,
    }

    @asset(config_schema={"logical_version": str})
    def alpha(context: OpExecutionContext):
        executed["alpha"] += 1
        return Output(1, logical_version=LogicalVersion(context.op_config["logical_version"]))

    @asset
    def beta(context, alpha):
        executed["beta"] += 1

    with instance_for_test() as instance:
        materialize_assets([alpha, beta], instance, _get_logical_version_config(alpha="foo"))
        assert executed["alpha"] == 1
        assert executed["beta"] == 1

        materialize_assets([alpha, beta], instance, _get_logical_version_config(alpha="bar"))
        assert executed["alpha"] == 2
        assert executed["beta"] == 2

        materialize_assets([alpha, beta], instance, _get_logical_version_config(alpha="bar"))
        assert executed["alpha"] == 3
        assert executed["beta"] == 2


# def test_return_asset_observation_from_materialize_fn():
#     @asset(config_schema={"logical_version": str})
#     def alpha(context: OpExecutionContext):
#         return AssetObservation
