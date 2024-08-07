import re
from datetime import datetime, timedelta
from random import randint
from unittest import mock

import pytest
from dagster import (
    AssetIn,
    AssetMaterialization,
    AssetOut,
    DagsterInstance,
    MaterializeResult,
    RunConfig,
    SourceAsset,
    asset,
    materialize,
    observable_source_asset,
)
from dagster._config.field import Field
from dagster._config.pythonic_config import Config
from dagster._core.definitions.data_version import (
    DATA_VERSION_TAG,
    SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD,
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
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey, Output
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.partition_mapping import AllPartitionMapping
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._utils import Counter, traced_counter
from dagster._utils.test.data_versions import (
    assert_code_version,
    assert_data_version,
    assert_different_versions,
    assert_provenance_match,
    assert_provenance_no_match,
    assert_same_versions,
    get_stale_status_resolver,
    get_upstream_version_from_mat_provenance,
    materialize_asset,
    materialize_assets,
    materialize_twice,
)

from dagster_tests.core_tests.instance_tests.test_instance_data_versions import (
    create_test_event_log_entry,
)

# ########################
# ##### TESTS
# ########################


def test_single_asset():
    @asset
    def asset1(): ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_single_versioned_asset():
    @asset(code_version="abc")
    def asset1(): ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([asset1], asset1, instance)
    assert_same_versions(mat1, mat2, "abc")


def test_source_asset_non_versioned_asset():
    source1 = SourceAsset("source1")

    @asset
    def asset1(source1): ...

    instance = DagsterInstance.ephemeral()
    mat1, mat2 = materialize_twice([source1, asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_source_asset_versioned_asset():
    source1 = SourceAsset("source1")

    @asset(code_version="abc")
    def asset1(source1): ...

    instance = DagsterInstance.ephemeral()

    mat1, mat2 = materialize_twice([source1, asset1], asset1, instance)
    assert_same_versions(mat1, mat2, "abc")


def test_source_asset_non_versioned_asset_deps():
    source1 = SourceAsset("source1")

    @asset(deps=[source1])
    def asset1(): ...

    instance = DagsterInstance.ephemeral()

    mat1, mat2 = materialize_twice([source1, asset1], asset1, instance)
    assert_different_versions(mat1, mat2)


def test_versioned_after_unversioned():
    source1 = SourceAsset("source1")

    @asset
    def asset1(source1): ...

    @asset(code_version="abc")
    def asset2(asset1): ...

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
    def asset1(source1): ...

    @asset(code_version="xyz")
    def asset2(asset1): ...

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
    def asset1(source1): ...

    @asset
    def asset2(asset1): ...

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
        outputs_to_return = sorted(context.op_execution_context.selected_output_names)
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
    def asset1(source1): ...

    @asset(code_version="xyz")
    def asset2(asset1): ...

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
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        materialize_assets(all_assets, instance)

        # Simulate updating an asset with a new code version
        @asset(name="asset1", code_version="def")
        def asset1_v2(source1): ...

        all_assets_v2 = [source1, asset1_v2, asset2]

        status_resolver = get_stale_status_resolver(instance, all_assets_v2)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_causes(asset1.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH

        @asset
        def asset3(): ...

        @asset(name="asset2", code_version="xyz")
        def asset2_v2(asset3): ...

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
    def asset1(): ...

    @asset
    def asset2(asset1): ...

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
    def asset1(): ...

    @asset
    def asset2(asset1): ...

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


def test_stale_status_dependency_partitions_count_over_threshold() -> None:
    partitions_def = StaticPartitionsDefinition(
        [str(x) for x in range(SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD)]
    )

    @asset(partitions_def=partitions_def)
    def asset1(context):
        keys = partitions_def.get_partition_keys_in_range(context.asset_partition_key_range)
        return {key: randint(0, 100) for key in keys}

    @asset
    def asset2(asset1): ...

    @asset
    def asset3(asset1): ...

    all_assets = [asset1, asset2, asset3]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "0") == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key) == StaleStatus.MISSING
        assert status_resolver.get_status(asset3.key) == StaleStatus.MISSING

        materialize_assets(
            [asset1, asset2],
            tags={
                ASSET_PARTITION_RANGE_START_TAG: "0",
                ASSET_PARTITION_RANGE_END_TAG: str(
                    SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD - 1
                ),
            },
            instance=instance,
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "0") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key) == StaleStatus.MISSING

        materialize_asset(all_assets, asset3, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH

        # Downstream values are not stale even after upstream changed because we are over threshold
        materialize_asset(all_assets, asset1, instance, partition_key="0")
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "0") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH


def test_stale_status_partitions_disabled_code_versions() -> None:
    partitions_def = StaticPartitionsDefinition(["foo"])

    @asset(code_version="1", partitions_def=partitions_def)
    def asset1(): ...

    @asset(code_version="1", partitions_def=partitions_def)
    def asset2(asset1): ...

    all_assets = [asset1, asset2]
    with instance_for_test() as instance:
        materialize_assets([asset1, asset2], partition_key="foo", instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "foo") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key, "foo") == StaleStatus.FRESH

        @asset(code_version="2", partitions_def=partitions_def)
        def asset1(): ...

        all_assets = [asset1, asset2]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "foo") == StaleStatus.STALE
        assert status_resolver.get_status(asset2.key, "foo") == StaleStatus.FRESH


def test_stale_status_partitions_enabled() -> None:
    partitions_def = StaticPartitionsDefinition(["foo"])

    class AssetConfig(Config):
        value: int = 1

    @asset(partitions_def=partitions_def)
    def asset1(config: AssetConfig):
        return Output(config.value, data_version=DataVersion(str(config.value)))

    @asset(partitions_def=partitions_def)
    def asset2(asset1): ...

    @asset
    def asset3(asset1): ...

    all_assets = [asset1, asset2, asset3]
    with instance_for_test() as instance:
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "foo") == StaleStatus.MISSING
        assert status_resolver.get_status(asset2.key, "foo") == StaleStatus.MISSING
        assert status_resolver.get_status(asset3.key) == StaleStatus.MISSING

        materialize_assets([asset1, asset2], partition_key="foo", instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "foo") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key, "foo") == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key) == StaleStatus.MISSING

        materialize_asset(all_assets, asset3, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH

        # Downstream values are not stale after upstream rematerialized with same version
        materialize_asset(
            all_assets,
            asset1,
            instance,
            partition_key="foo",
            run_config=RunConfig({"asset1": AssetConfig(value=1)}),
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "foo") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key, "foo") == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH

        # Downstream values are not stale after upstream rematerialized with same version
        materialize_asset(
            all_assets,
            asset1,
            instance,
            partition_key="foo",
            run_config=RunConfig({"asset1": AssetConfig(value=2)}),
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "foo") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key, "foo") == StaleStatus.STALE
        assert status_resolver.get_status(asset3.key) == StaleStatus.STALE


def test_stale_status_downstream_of_all_partitions_mapping():
    start_date = datetime(2020, 1, 1)
    end_date = start_date + timedelta(days=2)
    start_key = start_date.strftime("%Y-%m-%d")

    partitions_def = DailyPartitionsDefinition(start_date=start_date, end_date=end_date)

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    @asset(
        ins={"asset1": AssetIn(partition_mapping=AllPartitionMapping())},
    )
    def asset2(asset1):
        return 2

    all_assets = [asset1, asset2]

    # Downstream values are not stale even after upstream changed because of the partition mapping
    with instance_for_test() as instance:
        for k in partitions_def.get_partition_keys():
            materialize_asset(all_assets, asset1, instance, partition_key=k)

        materialize_asset(all_assets, asset2, instance)

        status_resolver = get_stale_status_resolver(instance, all_assets)
        for k in partitions_def.get_partition_keys():
            assert status_resolver.get_status(asset1.key, k) == StaleStatus.FRESH

        assert status_resolver.get_status(asset2.key, None) == StaleStatus.FRESH

        materialize_asset(
            all_assets,
            asset1,
            instance,
            partition_key=start_key,
        )

        status_resolver = get_stale_status_resolver(instance, all_assets)

        # Still fresh b/c of the partition mapping
        assert status_resolver.get_status(asset2.key, None) == StaleStatus.FRESH


def test_stale_status_many_to_one_partitions() -> None:
    partitions_def = StaticPartitionsDefinition(["alpha", "beta"])

    class AssetConfig(Config):
        value: int = 1

    @asset(partitions_def=partitions_def, code_version="1")
    def asset1(config: AssetConfig):
        return Output(1, data_version=DataVersion(str(config.value)))

    @asset(code_version="1")
    def asset2(asset1): ...

    @asset(partitions_def=partitions_def, code_version="1")
    def asset3(asset2):
        return 1

    a1_alpha_key = AssetKeyPartitionKey(asset1.key, "alpha")
    a1_beta_key = AssetKeyPartitionKey(asset1.key, "beta")

    all_assets = [asset1, asset2, asset3]
    with instance_for_test() as instance:
        for key in partitions_def.get_partition_keys():
            materialize_asset(
                all_assets,
                asset1,
                instance,
                partition_key=key,
            )
        materialize_asset(all_assets, asset2, instance)

        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "alpha") == StaleStatus.FRESH
        assert status_resolver.get_status(asset1.key, "beta") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key, "alpha") == StaleStatus.MISSING

        for key in partitions_def.get_partition_keys():
            materialize_asset(
                all_assets,
                asset3,
                instance,
                partition_key=key,
            )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset3.key, "alpha") == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key, "beta") == StaleStatus.FRESH

        materialize_asset(
            all_assets,
            asset1,
            instance,
            partition_key="alpha",
            run_config=RunConfig({"asset1": AssetConfig(value=2)}),
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key, "alpha") == StaleStatus.FRESH
        assert status_resolver.get_status(asset1.key, "beta") == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_status(asset3.key, "alpha") == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key, "beta") == StaleStatus.FRESH
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DATA,
                "has a new dependency data version",
                a1_alpha_key,
                [
                    StaleCause(a1_alpha_key, StaleCauseCategory.DATA, "has a new data version"),
                ],
            )
        ]

        # Now both partitions should show up in stale reasons
        materialize_asset(
            all_assets,
            asset1,
            instance,
            partition_key="beta",
            run_config=RunConfig({"asset1": AssetConfig(value=2)}),
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_stale_causes(asset2.key) == [
            StaleCause(
                asset2.key,
                StaleCauseCategory.DATA,
                "has a new dependency data version",
                dep_key,
                [
                    StaleCause(dep_key, StaleCauseCategory.DATA, "has a new data version"),
                ],
            )
            for dep_key in [a1_alpha_key, a1_beta_key]
        ]
        assert status_resolver.get_status(asset3.key, "alpha") == StaleStatus.FRESH

        materialize_asset(all_assets, asset2, instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset3.key, "alpha") == StaleStatus.STALE
        assert status_resolver.get_status(asset3.key, "beta") == StaleStatus.STALE


@pytest.mark.parametrize(
    ("num_partitions", "expected_status"),
    [
        (2, StaleStatus.STALE),  # under threshold
        (3, StaleStatus.FRESH),  # over threshold
    ],
)
def test_stale_status_self_partitioned(num_partitions: int, expected_status: StaleStatus) -> None:
    start_date = datetime(2020, 1, 1)
    end_date = start_date + timedelta(days=num_partitions)

    partitions_def = DailyPartitionsDefinition(start_date=start_date, end_date=end_date)
    start_key = start_date.strftime("%Y-%m-%d")
    end_key = (end_date - timedelta(days=1)).strftime("%Y-%m-%d")

    @asset(
        partitions_def=partitions_def,
        ins={
            "asset1": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            )
        },
    )
    def asset1(asset1):
        return 1 if asset1 is None else asset1 + 1

    all_assets = [asset1]
    with instance_for_test() as instance:
        for k in partitions_def.get_partition_keys():
            materialize_asset(all_assets, asset1, instance, partition_key=k)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        for k in partitions_def.get_partition_keys():
            assert status_resolver.get_status(asset1.key, k) == StaleStatus.FRESH

        materialize_asset(
            all_assets,
            asset1,
            instance,
            partition_key=start_key,
        )
        status_resolver = get_stale_status_resolver(instance, all_assets)
        with mock.patch(
            "dagster._core.definitions.data_version.SKIP_PARTITION_DATA_VERSION_SELF_DEPENDENCY_THRESHOLD",
            3,
        ):
            # In the under-threshold case, this should return STALE since we updated an upstream
            # partition.
            #
            # In the over-threshold case, even though we introduced a new data version to an
            # upstream partition, this should return FRESH because the number of self-partitions is
            # > SKIP_PARTITION_DATA_VERSION_SELF_DEPENDENCY_THRESHOLD
            assert status_resolver.get_status(asset1.key, end_key) == expected_status


def test_stale_status_manually_versioned() -> None:
    @asset(config_schema={"value": Field(int)})
    def asset1(context):
        value = context.op_execution_context.op_config["value"]
        return Output(value, data_version=DataVersion(str(value)))

    @asset(config_schema={"value": Field(int)})
    def asset2(context, asset1):
        value = context.op_execution_context.op_config["value"] + asset1
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


def test_stale_status_non_transitive_root_causes() -> None:
    x = 0

    @observable_source_asset
    def source1(_context):
        nonlocal x
        x = x + 1
        return DataVersion(str(x))

    @asset(code_version="1")
    def asset1(source1): ...

    @asset(code_version="1")
    def asset2(asset1): ...

    @asset(code_version="1")
    def asset3(asset2): ...

    with instance_for_test() as instance:
        all_assets = [source1, asset1, asset2, asset3]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_stale_root_causes(asset1.key) == []
        assert status_resolver.get_stale_root_causes(asset2.key) == []

        materialize_assets(all_assets, instance)

        # Simulate updating an asset with a new code version
        @asset(name="asset1", code_version="2")
        def asset1_v2(source1): ...

        all_assets = [source1, asset1_v2, asset2, asset3]
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset1.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version")
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_stale_root_causes(asset2.key) == []
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH
        assert status_resolver.get_stale_root_causes(asset3.key) == []

        observe([source1], instance=instance)
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset1.key) == [
            StaleCause(asset1.key, StaleCauseCategory.CODE, "has a new code version"),
            StaleCause(source1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]
        assert status_resolver.get_status(asset2.key) == StaleStatus.FRESH
        assert status_resolver.get_stale_root_causes(asset2.key) == []
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH
        assert status_resolver.get_stale_root_causes(asset3.key) == []

        materialize_assets(all_assets, instance=instance, selection=[asset1])
        status_resolver = get_stale_status_resolver(instance, all_assets)
        assert status_resolver.get_status(asset1.key) == StaleStatus.FRESH
        assert status_resolver.get_status(asset2.key) == StaleStatus.STALE
        assert status_resolver.get_stale_root_causes(asset2.key) == [
            StaleCause(asset1.key, StaleCauseCategory.DATA, "has a new data version"),
        ]
        assert status_resolver.get_status(asset3.key) == StaleStatus.FRESH
        assert status_resolver.get_stale_root_causes(asset3.key) == []


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
        if context.op_execution_context.op_config["check_provenance"]:
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
            input_storage_ids={AssetKey(["foo"]): 4},
            is_user_provided=True,
        )


def test_stale_cause_comparison():
    cause_1 = StaleCause(key=AssetKey(["foo"]), category=StaleCauseCategory.CODE, reason="ok")

    cause_2 = StaleCause(key=AssetKey(["foo"]), category=StaleCauseCategory.DATA, reason="ok")

    assert cause_1 < cause_2


# This test what happens if an "off-books" materialization of an upstream asset used in provenance
# tracking occurs during a step. Here we use a `yield AssetMaterialization`, but this can also
# represent an SDA-style materialization generated by a parallel run. If the data version matches
# the step-internal materialization, no warning is emitted. If it does not match, a warning is
# emitted and the most recent materialization is used for provenance.
def test_most_recent_materialization_used(capsys):
    class FooBarConfig(Config):
        external_foo_data_version: str

    @multi_asset(
        outs={"foo": AssetOut(), "bar": AssetOut()},
        internal_asset_deps={"foo": set(), "bar": {AssetKey("foo")}},
    )
    def foo_bar(config: FooBarConfig):
        yield Output(1, output_name="foo", data_version=DataVersion("alpha"))
        yield AssetMaterialization(
            asset_key=AssetKey("foo"), tags={DATA_VERSION_TAG: config.external_foo_data_version}
        )
        yield Output(2, output_name="bar")

    with instance_for_test() as instance:
        materialize(
            [foo_bar],
            instance=instance,
            run_config={"ops": {"foo_bar": {"config": {"external_foo_data_version": "beta"}}}},
        )
        captured = capsys.readouterr()
        message = "Data version mismatch"
        assert re.search(message, captured.err, re.MULTILINE)
        mat = instance.get_latest_materialization_event(AssetKey("bar"))
        assert mat and mat.asset_materialization
        assert (
            get_upstream_version_from_mat_provenance(mat.asset_materialization, AssetKey("foo"))
            == "beta"
        )


def test_materialize_result_overwrite_provenance_tag():
    @asset
    def asset0(): ...

    @asset(deps=["asset0"])
    def asset1():
        return MaterializeResult(tags={"dagster/input_event_pointer/asset0": 500})

    with instance_for_test() as instance:
        materialize([asset0], instance=instance)
        materialize([asset1], instance=instance)

        record = instance.get_latest_data_version_record(asset1.key)
        assert extract_data_provenance_from_entry(record.event_log_entry).input_storage_ids == {
            AssetKey(["asset0"]): 500
        }


def test_output_overwrite_provenance_tag():
    @asset
    def asset0(): ...

    @asset(deps=["asset0"])
    def asset1():
        return Output(value=None, tags={"dagster/input_event_pointer/asset0": 500})

    with instance_for_test() as instance:
        materialize([asset0], instance=instance)
        materialize([asset1], instance=instance)

        record = instance.get_latest_data_version_record(asset1.key)
        assert extract_data_provenance_from_entry(record.event_log_entry).input_storage_ids == {
            AssetKey(["asset0"]): 500
        }


def test_fan_in():
    def create_upstream_asset(i: int):
        @asset(name=f"upstream_asset_{i}", code_version="abc")
        def upstream_asset():
            return i

        return upstream_asset

    upstream_assets = [create_upstream_asset(i) for i in range(100)]

    @asset(
        ins={f"input_{i}": AssetIn(key=f"upstream_asset_{i}") for i in range(100)},
        code_version="abc",
    )
    def downstream_asset(**kwargs):
        return kwargs.values()

    all_assets = [*upstream_assets, downstream_asset]
    instance = DagsterInstance.ephemeral()
    materialize_assets(all_assets, instance)

    counter = Counter()
    traced_counter.set(counter)
    materialize_assets(all_assets, instance)[downstream_asset.key]
    assert traced_counter.get().counts() == {
        "DagsterInstance.get_asset_records": 1,
        "DagsterInstance.get_run_record_by_id": 1,
    }
