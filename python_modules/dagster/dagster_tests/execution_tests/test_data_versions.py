from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union, cast, overload
from unittest import mock

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
from dagster._config.field import Field
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.data_version import (
    CODE_VERSION_TAG,
    DATA_VERSION_TAG,
    INPUT_DATA_VERSION_TAG_PREFIX,
    CachingStaleStatusResolver,
    DataProvenance,
    DataVersion,
    StaleCause,
    StaleCauseCategory,
    StaleStatus,
    compute_logical_data_version,
    extract_data_provenance_from_entry,
    extract_data_version_from_entry,
)
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import AssetKey, Output
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance_for_test import instance_for_test
from typing_extensions import Literal

from dagster_tests.core_tests.instance_tests.test_instance_data_versions import (
    create_test_event_log_entry,
)

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
    partition_key: Optional[str] = None,
    run_config: Optional[Mapping[str, Any]] = None,
) -> MaterializationTable:
    ...


@overload
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    *,
    is_multi: Literal[False] = ...,
    partition_key: Optional[str] = None,
    run_config: Optional[Mapping[str, Any]] = None,
) -> AssetMaterialization:
    ...


# Use only for AssetsDefinition with one asset
def materialize_asset(
    all_assets: Sequence[Union[AssetsDefinition, SourceAsset]],
    asset_to_materialize: AssetsDefinition,
    instance: DagsterInstance,
    *,
    is_multi: bool = False,
    partition_key: Optional[str] = None,
    run_config: Optional[Mapping[str, Any]] = None,
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
) -> MaterializationTable:
    result = materialize(
        assets,
        instance=instance,
        resources={"io_manager": mock_io_manager},
        partition_key=partition_key,
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


def test_source_asset_non_versioned_asset_deps():
    source1 = SourceAsset("source1")

    @asset(deps=[source1])
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

    assert_data_version(alpha_mat, compute_logical_data_version("a", {}))
    assert_code_version(alpha_mat, "a")
    assert_data_version(beta_mat, compute_logical_data_version("b", {}))
    assert_code_version(beta_mat, "b")


def test_set_data_version_inside_op():
    instance = DagsterInstance.ephemeral()

    @asset
    def asset1():
        return Output(1, data_version=DataVersion("foo"))

    mat = materialize_asset([asset1], asset1, instance)
    assert_data_version(mat, DataVersion("foo"))


def test_stale_status_general() -> None:
    x = 0

    @observable_source_asset
    def source1(_context):
        nonlocal x
        x = x + 1
        return DataVersion(str(x))

    @asset(code_version="abc")
    def asset1(source1):
        ...

    @asset(code_version="xyz")
    def asset2(asset1):
        ...

    all_assets = [source1, asset1, asset2]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(source1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset1.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key) == StaleStatus.MISSING
        assert status_resolver.get_stale_causes(source1.key) == []
        assert status_resolver.get_stale_causes(asset1.key) == []
        assert status_resolver.get_stale_causes(asset2.key) == []

        materialize_assets(all_assets, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH

        observe([source1], instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset1.key) == [
            StaleCause(
                asset1.key,
                StaleCauseCategory.DATA,
                "has a new dependency data version",
                source1.key,
                [
                    StaleCause(source1.key, StaleCauseCategory.DATA, "has a new data version"),
                ],
            ),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DATA,
                "stale dependency",
                asset1.key,
                [
                    StaleCause(
                        asset1.key,
                        StaleCauseCategory.DATA,
                        "has a new dependency data version",
                        source1.key,
                        [
                            StaleCause(
                                source1.key, StaleCauseCategory.DATA, "has a new data version"
                            ),
                        ],
                    ),
                ],
            )
        ]
        materialize_assets(all_assets, instance)

        # Simulate updating an asset with a new code version
        @asset(name="asset1", code_version="def")
        def asset1_v2(source1):
            ...

        all_assets_v2 = [source1, asset1_v2, asset2]

        status_resolver = get_stale_status_resolver(instance, all_assets_v2)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset1.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DATA,
                "stale dependency",
                asset1.key,
                [
                    StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
                ],
            ),
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
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DEPENDENCIES,
                "removed dependency on asset1",
                asset1.key,
            ),
            StaleCause(
                asset2.key,
                StaleCauseCategory.DEPENDENCIES,
                "has a new dependency on asset3",
                asset3.key,
            ),
        ]


def test_stale_status_no_code_versions() -> None:
    @asset
    def asset1():
        ...

    @asset
    def asset2(asset1):
        ...

    all_assets = [asset1, asset2]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key) == StaleStatus.MISSING

        materialize_assets(all_assets, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH

        materialize_asset(all_assets, asset1, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DATA,
                "has a new dependency materialization",
                asset1.key,
                [
                    StaleCause(asset1.key, StaleCauseCategory.DATA, "has a new materialization"),
                ],
            ),
        ]

        materialize_asset(all_assets, asset2, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH


def test_stale_status_redundant_upstream_materialization() -> None:
    @asset(code_version="abc")
    def asset1():
        ...

    @asset
    def asset2(asset1):
        ...

    all_assets = [asset1, asset2]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key) == StaleStatus.MISSING

        materialize_assets(all_assets, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH

        materialize_asset(all_assets, asset1, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH


def test_stale_status_partitioned() -> None:
    partitions_def = StaticPartitionsDefinition(["foo"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset(partitions_def=partitions_def)
    def asset2(asset1):
        ...

    @asset
    def asset3(asset1):
        ...

    all_assets = [asset1, asset2, asset3]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset3.key) == StaleStatus.MISSING

        materialize_assets([asset1, asset2], partition_key="foo", instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key) == StaleStatus.MISSING

        materialize_asset(all_assets, asset3, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH

        # Downstream values are not stale even after upstream changed
        materialize_asset(all_assets, asset1, instance, partition_key="foo")
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH


def test_stale_status_manually_versioned() -> None:
    @asset(config_schema={"value": Field(int)})
    def asset1(context):
        value = context.op_config["value"]
        return Output(value, data_version=DataVersion(str(value)))

    @asset(config_schema={"value": Field(int)})
    def asset2(context, asset1):
        value = context.op_config["value"] + asset1
        return Output(value, data_version=DataVersion(str(value)))

    all_assets = [asset1, asset2]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key) == StaleStatus.MISSING

        materialize_assets(
            [asset1, asset2],
            instance=instance,
            run_config={
                "ops": {"asset1": {"config": {"value": 1}}, "asset2": {"config": {"value": 1}}}
            },
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH

        materialize_asset(
            [asset1],
            asset1,
            instance=instance,
            run_config={"ops": {"asset1": {"config": {"value": 2}}}},
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DATA,
                "has a new dependency data version",
                asset1.key,
                [
                    StaleCause(asset1.key, StaleCauseCategory.DATA, "has a new data version"),
                ],
            ),
        ]

        # rematerialize with the old value, asset2 should be fresh again
        materialize_asset(
            [asset1],
            asset1,
            instance=instance,
            run_config={"ops": {"asset1": {"config": {"value": 1}}}},
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH


def test_stale_status_root_causes_general() -> None:
    x = 0

    @observable_source_asset
    def source1(_context):
        nonlocal x
        x = x + 1
        return DataVersion(str(x))

    @asset(code_version="1")
    def asset1(source1):
        ...

    @asset(code_version="1")
    def asset2(asset1):
        ...

    @asset(code_version="1")
    def asset3(asset2):
        ...

    with instance_for_test() as instance:
        all_assets = [source1, asset1, asset2, asset3]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_stale_root_causes(asset1.key) == []
        assert status_resolver.get_stale_root_causes(asset2.key) == []

        materialize_assets(all_assets, instance)

        # Simulate updating an asset with a new code version
        @asset(name="asset1", code_version="2")
        def asset1_v2(source1):
            ...

        all_assets = [source1, asset1_v2, asset2, asset3]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset1.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version")
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset2.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version")
        ]
        assert status_resolver.get_status(asset3.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset3.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version")
        ]

        observe([source1], instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset1.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
            StaleCause(source1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset2.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
            StaleCause(source1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]
        assert status_resolver.get_status(asset3.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset3.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
            StaleCause(source1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]

        # Simulate updating an asset with a new code version
        @asset(name="asset3", code_version="2")
        def asset3_v2(asset2):
            ...

        all_assets = [source1, asset1_v2, asset2, asset3_v2]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_stale_root_causes(asset3.key) == [
            StaleCause(asset3.key, StaleCauseCategory.CODE, "has a new code version"),
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
            StaleCause(source1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]


def test_stale_status_root_causes_dedup() -> None:
    x = 0

    @asset(code_version="1")
    def asset1():
        nonlocal x
        x += 1
        return Output(x, data_version=DataVersion(str(x)))

    @asset
    def asset2(asset1):
        ...

    @asset
    def asset3(asset1):
        ...

    @asset
    def asset4(asset2, asset3):
        ...

    with instance_for_test() as instance:
        all_assets = [asset1, asset2, asset3, asset4]
        materialize_assets(all_assets, instance)

        # Test dedup from updated data version
        materialize_assets([asset1], instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_stale_root_causes(asset4.key) == [
            StaleCause(asset1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]

        # Test dedup from updated code version
        @asset(name="asset1", code_version="2")
        def asset1_v2():
            ...

        all_assets = [asset1_v2, asset2, asset3, asset4]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_stale_root_causes(asset4.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
        ]


def test_no_provenance_stale_status():
    @asset
    def foo(bar):
        return 1

    bar = SourceAsset(AssetKey(["bar"]))

    with instance_for_test() as instance:
        materialization = AssetMaterialization(asset_key=AssetKey(["foo"]))
        entry = create_test_event_log_entry(DagsterEventType.ASSET_MATERIALIZATION, materialization)
        instance.store_event(entry)
        status_resolver = get_stale_status_resolver(instance, [foo, bar])
        assert status_resolver.get_status(foo.key) == StaleStatus.FRESH
        assert status_resolver.get_stale_root_causes(foo.key) == []


def test_get_data_provenance_inside_op():
    instance = DagsterInstance.ephemeral()

    @asset
    def asset1():
        return Output(1, data_version=DataVersion("foo"))

    @asset(config_schema={"check_provenance": Field(bool, default_value=False)})
    def asset2(context: AssetExecutionContext, asset1):
        if context.op_config["check_provenance"]:
            provenance = context.get_asset_provenance(AssetKey("asset2"))
            assert provenance
            assert provenance.input_data_versions[AssetKey("asset1")] == DataVersion("foo")
        return Output(2)

    mats = materialize_assets([asset1, asset2], instance)
    assert_data_version(mats["asset1"], DataVersion("foo"))
    materialize_asset(
        [asset1, asset2],
        asset2,
        instance,
        run_config={"ops": {"asset2": {"config": {"check_provenance": True}}}},
    )


# use old logical version tags
def test_legacy_data_version_tags():
    @asset
    def foo():
        return Output(1, data_version=DataVersion("alpha"))

    @asset(code_version="1")
    def bar(foo):
        return Output(foo + 1, data_version=DataVersion("beta"))

    with instance_for_test() as instance:

        def mocked_get_input_data_version_tag(
            input_key: AssetKey, prefix: str = "dagster/input_logical_version"
        ) -> str:
            return f"{prefix}/{input_key.to_user_string()}"

        legacy_tags = {
            "DATA_VERSION_TAG": "dagster/logical_version",
            "get_input_data_version_tag": mocked_get_input_data_version_tag,
        }

        # This will create materializations with the legacy tags
        with mock.patch.dict("dagster._core.execution.plan.execute_step.__dict__", legacy_tags):
            mats = materialize_assets([foo, bar], instance)
            assert mats["bar"].tags["dagster/logical_version"]
            assert mats["bar"].tags["dagster/input_logical_version/foo"]
            assert mats["bar"].tags["dagster/input_event_pointer/foo"]

        # We're now outside the mock context
        record = instance.get_latest_data_version_record(bar.key)
        assert record
        assert extract_data_version_from_entry(record.event_log_entry) == DataVersion("beta")
        assert extract_data_provenance_from_entry(record.event_log_entry) == DataProvenance(
            code_version="1",
            input_data_versions={AssetKey(["foo"]): DataVersion("alpha")},
            is_user_provided=True,
        )


def test_stale_cause_comparison():
    cause_1 = StaleCause(key=AssetKey(["foo"]), category=StaleCauseCategory.CODE, reason="ok")

    cause_2 = StaleCause(key=AssetKey(["foo"]), category=StaleCauseCategory.DATA, reason="ok")

    assert cause_1 < cause_2
