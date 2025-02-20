import os
import re
import sys
import time
from unittest import mock

import pytest
from dagster import (
    AssetIn,
    AssetKey,
    AssetSpec,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    IdentityPartitionMapping,
    SourceAsset,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    asset,
    graph_asset,
    multi_asset,
    op,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.remote_representation import InProcessCodeLocationOrigin
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    CurrentWorkspace,
)


@asset
def asset1(): ...


defs1 = Definitions(assets=[asset1])


@asset
def asset2(): ...


defs2 = Definitions(assets=[asset2])


asset1_source = SourceAsset("asset1")


@asset
def downstream(asset1):
    del asset1


downstream_defs = Definitions(assets=[asset1_source, downstream])


@asset(deps=[asset1])
def downstream_non_arg_dep(): ...


downstream_defs_no_source = Definitions(assets=[downstream_non_arg_dep])

partitioned_source = SourceAsset(
    "partitioned_source", partitions_def=DailyPartitionsDefinition(start_date="2022-01-01")
)


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    deps=[partitioned_source],
    auto_materialize_policy=AutoMaterializePolicy.eager(
        max_materializations_per_minute=75,
    ),
)
def downstream_of_partitioned_source():
    pass


@observable_source_asset(partitions_def=DailyPartitionsDefinition(start_date="2011-01-01"))
def partitioned_observable_source1():
    pass


@observable_source_asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
def partitioned_observable_source2():
    pass


partitioned_defs = Definitions(
    assets=[
        partitioned_source,
        downstream_of_partitioned_source,
        partitioned_observable_source1,
        partitioned_observable_source2,
    ]
)

static_partition = partitions_def = StaticPartitionsDefinition(["foo", "bar"])


@pytest.fixture
def instance():
    with instance_for_test() as the_instance:
        yield the_instance


@asset(
    partitions_def=static_partition,
)
def static_partitioned_asset():
    pass


@asset(
    partitions_def=static_partition,
)
def other_static_partitioned_asset():
    pass


different_partitions_defs = Definitions(
    assets=[
        static_partitioned_asset,
        other_static_partitioned_asset,
        downstream_of_partitioned_source,
        partitioned_source,
    ]
)


def _make_location_entry(defs_attr: str, instance: DagsterInstance):
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=__file__,
            working_directory=os.path.dirname(__file__),
            attribute=defs_attr,
        ),
        container_image=None,
        entry_point=None,
        container_context=None,
        location_name=None,
    )

    code_location = origin.create_location(instance)

    return CodeLocationEntry(
        origin=origin,
        code_location=code_location,
        load_error=None,
        load_status=CodeLocationLoadStatus.LOADED,
        display_metadata={},
        update_timestamp=time.time(),
        version_key="test",
    )


def _make_context(instance: DagsterInstance, defs_attrs):
    return WorkspaceRequestContext(
        instance=mock.MagicMock(),
        current_workspace=CurrentWorkspace(
            code_location_entries={
                defs_attr: _make_location_entry(defs_attr, instance) for defs_attr in defs_attrs
            }
        ),
        process_context=mock.MagicMock(),
        version=None,
        source=None,
        read_only=True,
    )


def test_get_repository_selector(instance) -> None:
    asset_graph = _make_context(instance, ["defs1", "defs2"]).asset_graph

    assert asset_graph.get_materialization_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle1 = asset_graph.get_repository_handle(asset1.key)
    assert repo_handle1.repository_name == "__repository__"

    assert asset_graph.get_materialization_job_names(asset1.key) == ["__ASSET_JOB"]
    repo_handle2 = asset_graph.get_repository_handle(asset2.key)
    assert repo_handle2.repository_name == "__repository__"


def test_cross_repo_dep_with_source_asset(instance) -> None:
    asset_graph = _make_context(instance, ["defs1", "downstream_defs"]).asset_graph

    assert len(asset_graph.external_asset_keys) == 0
    assert asset_graph.get(AssetKey("downstream")).parent_keys == {AssetKey("asset1")}
    assert asset_graph.get(AssetKey("asset1")).child_keys == {AssetKey("downstream")}

    assert asset_graph.get_materialization_job_names(AssetKey("asset1")) == ["__ASSET_JOB"]

    assert asset_graph.get_materialization_job_names(AssetKey("downstream")) == ["__ASSET_JOB"]


def test_cross_repo_dep_no_source_asset(instance) -> None:
    asset_graph = _make_context(instance, ["defs1", "downstream_defs_no_source"]).asset_graph
    assert len(asset_graph.external_asset_keys) == 0
    assert asset_graph.get(AssetKey("downstream_non_arg_dep")).parent_keys == {AssetKey("asset1")}
    assert asset_graph.get(AssetKey("asset1")).child_keys == {AssetKey("downstream_non_arg_dep")}

    assert asset_graph.get_materialization_job_names(AssetKey("asset1")) == ["__ASSET_JOB"]
    assert asset_graph.get_materialization_job_names(AssetKey("downstream_non_arg_dep")) == [
        "__ASSET_JOB"
    ]


def test_partitioned_source_asset(instance) -> None:
    asset_graph = _make_context(instance, ["partitioned_defs"]).asset_graph

    assert asset_graph.get(AssetKey("partitioned_source")).is_partitioned
    assert asset_graph.get(AssetKey("downstream_of_partitioned_source")).is_partitioned


def test_auto_materialize_policy(instance) -> None:
    asset_graph = _make_context(instance, ["partitioned_defs"]).asset_graph

    assert asset_graph.get(
        AssetKey("downstream_of_partitioned_source")
    ).auto_materialize_policy == AutoMaterializePolicy.eager(
        max_materializations_per_minute=75,
    )


@asset(
    ins={
        "static_partitioned_asset": AssetIn(
            partition_mapping=StaticPartitionMapping({"foo": "1", "bar": "2"})
        )
    },
    partitions_def=StaticPartitionsDefinition(["1", "2"]),
)
def partition_mapping_asset(static_partitioned_asset):
    pass


partition_mapping_defs = Definitions(assets=[static_partitioned_asset, partition_mapping_asset])


def test_partition_mapping(instance) -> None:
    asset_graph = _make_context(instance, ["partition_mapping_defs"]).asset_graph

    assert isinstance(
        asset_graph.get_partition_mapping(
            AssetKey("partition_mapping_asset"), AssetKey("static_partitioned_asset")
        ),
        StaticPartitionMapping,
    )
    assert isinstance(
        asset_graph.get_partition_mapping(
            AssetKey("static_partitioned_asset"), AssetKey("partition_mapping_asset")
        ),
        IdentityPartitionMapping,
    )


@asset(
    partitions_def=static_partition,
    backfill_policy=BackfillPolicy.single_run(),
)
def static_partitioned_single_run_backfill_asset():
    pass


@asset(
    partitions_def=None,
    backfill_policy=BackfillPolicy.single_run(),
)
def non_partitioned_single_run_backfill_asset():
    pass


@asset(
    partitions_def=static_partition,
    backfill_policy=BackfillPolicy.multi_run(5),
)
def static_partitioned_multi_run_backfill_asset():
    pass


backfill_assets_defs = Definitions(
    assets=[
        static_partitioned_single_run_backfill_asset,
        non_partitioned_single_run_backfill_asset,
        static_partitioned_multi_run_backfill_asset,
    ]
)


def test_assets_with_backfill_policies(instance):
    asset_graph = _make_context(instance, ["backfill_assets_defs"]).asset_graph
    assert (
        asset_graph.get(AssetKey("static_partitioned_single_run_backfill_asset")).backfill_policy
        == BackfillPolicy.single_run()
    )
    assert (
        asset_graph.get(AssetKey("non_partitioned_single_run_backfill_asset")).backfill_policy
        == BackfillPolicy.single_run()
    )
    assert asset_graph.get(
        AssetKey("static_partitioned_multi_run_backfill_asset")
    ).backfill_policy == BackfillPolicy.multi_run(5)


@asset(deps=[SourceAsset("b")])
def a():
    pass


@asset(deps=[SourceAsset("a")])
def b():
    pass


cycle_defs_a = Definitions(assets=[a])
cycle_defs_b = Definitions(assets=[b])


def test_cycle_status(instance) -> None:
    context = _make_context(instance, ["cycle_defs_a", "cycle_defs_b"])
    asset_graph = context.asset_graph

    resolver = CachingStaleStatusResolver(DagsterInstance.ephemeral(), asset_graph, context)
    for key in asset_graph.get_all_asset_keys():
        resolver.get_status(key)


@asset
def single_materializable_asset(): ...


@observable_source_asset
def single_observable_asset(): ...


dup_materialization_defs_a = Definitions(assets=[single_materializable_asset])
dup_materialization_defs_b = Definitions(assets=[single_materializable_asset])
dup_observation_defs_a = Definitions(assets=[single_observable_asset])
dup_observation_defs_b = Definitions(assets=[single_observable_asset])


def test_dup_node_detection(instance):
    with pytest.warns(
        UserWarning,
        match=re.compile(
            r'Only one MATERIALIZATION node is allowed per asset.*"single_materializable_asset"',
            re.DOTALL,
        ),
    ):
        _ = _make_context(
            instance, ["dup_materialization_defs_a", "dup_materialization_defs_b"]
        ).asset_graph

    with pytest.warns(
        UserWarning,
        match=re.compile(
            r'Only one OBSERVATION node is allowed per asset.*"single_observable_asset"', re.DOTALL
        ),
    ):
        _ = _make_context(
            instance, ["dup_observation_defs_a", "dup_observation_defs_b"]
        ).asset_graph


@asset(pool="foo")
def my_asset():
    pass


@op(pool="bar")
def my_op():
    pass


@graph_asset
def my_graph_asset():
    return my_op()


@multi_asset(
    specs=[
        AssetSpec("multi_asset_1"),
        AssetSpec("multi_asset_2"),
    ],
    pool="baz",
)
def my_multi_asset():
    pass


concurrency_assets = Definitions(assets=[my_asset, my_graph_asset, my_multi_asset])


def test_pool_snap(instance) -> None:
    context = _make_context(instance, ["concurrency_assets"])
    asset_graph = context.asset_graph
    assert asset_graph
    assert asset_graph.get(AssetKey("my_asset")).pools == {"foo"}
    assert asset_graph.get(AssetKey("my_graph_asset")).pools == {"bar"}
    assert asset_graph.get(AssetKey("multi_asset_1")).pools == {"baz"}
    assert asset_graph.get(AssetKey("multi_asset_2")).pools == {"baz"}
