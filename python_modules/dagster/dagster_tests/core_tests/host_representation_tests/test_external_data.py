from typing import Dict

import pytest
from dagster import AssetKey, DagsterInvariantViolationError, In, Out, job, pipeline
from dagster.core.asset_defs import ForeignAsset, asset, build_assets_job
from dagster.core.decorator_utils import get_function_params
from dagster.core.definitions.decorators.op import _Op
from dagster.core.host_representation.external_data import (
    ExternalAssetDependedBy,
    ExternalAssetDependency,
    ExternalAssetNode,
    ExternalSensorData,
    ExternalTargetData,
    external_asset_graph_from_defs,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def test_single_asset_job():
    @asset
    def asset1():
        return 1

    assets_job = build_assets_job("assets_job", [asset1])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], foreign_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        )
    ]


def test_two_asset_job():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    assets_job = build_assets_job("assets_job", [asset1, asset2])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], foreign_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2"), input_name="asset1"
                )
            ],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_two_downstream_assets_job():
    @asset
    def asset1():
        return 1

    @asset
    def asset2_a(asset1):
        assert asset1 == 1

    @asset
    def asset2_b(asset1):
        assert asset1 == 1

    assets_job = build_assets_job("assets_job", [asset1, asset2_a, asset2_b])
    external_asset_nodes = external_asset_graph_from_defs([assets_job], foreign_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2_a"), input_name="asset1"
                ),
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2_b"), input_name="asset1"
                ),
            ],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2_a"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2_a",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2_b"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2_b",
            op_description=None,
            job_names=["assets_job"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_cross_job_asset_dependency():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    assets_job1 = build_assets_job("assets_job1", [asset1])
    assets_job2 = build_assets_job("assets_job2", [asset2], source_assets=[asset1])
    external_asset_nodes = external_asset_graph_from_defs(
        [assets_job1, assets_job2], foreign_assets_by_key={}
    )

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(
                    downstream_asset_key=AssetKey("asset2"), input_name="asset1"
                )
            ],
            op_name="asset1",
            op_description=None,
            job_names=["assets_job1"],
            output_name="result",
            output_description=None,
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=["assets_job2"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_same_asset_in_multiple_pipelines():
    @asset
    def asset1():
        return 1

    job1 = build_assets_job("job1", [asset1])
    job2 = build_assets_job("job2", [asset1])

    external_asset_nodes = external_asset_graph_from_defs([job1, job2], foreign_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[],
            op_name="asset1",
            op_description=None,
            job_names=["job1", "job2"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_basic_multi_asset():
    pass


def test_inter_op_dependency():
    pass


def test_unused_foreign_asset():
    foo = ForeignAsset(key=AssetKey("foo"), description="abc")
    bar = ForeignAsset(key=AssetKey("bar"), description="def")

    external_asset_nodes = external_asset_graph_from_defs(
        [], foreign_assets_by_key={AssetKey("foo"): foo, AssetKey("bar"): bar}
    )
    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("foo"),
            op_description="abc",
            dependencies=[],
            depended_by=[],
            job_names=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_description="def",
            dependencies=[],
            depended_by=[],
            job_names=[],
        ),
    ]


def test_used_foreign_asset():
    bar = ForeignAsset(key=AssetKey("bar"), description="def")

    @asset
    def foo(bar):
        assert bar

    job1 = build_assets_job("job1", [foo], source_assets=[bar])

    external_asset_nodes = external_asset_graph_from_defs(
        [job1], foreign_assets_by_key={AssetKey("bar"): bar}
    )
    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("bar"),
            op_description="def",
            dependencies=[],
            depended_by=[
                ExternalAssetDependedBy(downstream_asset_key=AssetKey(["foo"]), input_name="bar")
            ],
            job_names=[],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("foo"),
            op_name="foo",
            op_description=None,
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey(["bar"]), input_name="bar")
            ],
            depended_by=[],
            job_names=["job1"],
            output_name="result",
            output_description=None,
        ),
    ]


def test_foreign_asset_conflicts_with_asset():
    bar_foreign_asset = ForeignAsset(key=AssetKey("bar"), description="def")

    @asset
    def bar():
        pass

    job1 = build_assets_job("job1", [bar])

    with pytest.raises(DagsterInvariantViolationError):
        external_asset_graph_from_defs(
            [job1], foreign_assets_by_key={AssetKey("bar"): bar_foreign_asset}
        )


def test_back_compat_external_sensor():
    SERIALIZED_0_12_10_SENSOR = '{"__class__": "ExternalSensorData", "description": null, "min_interval": null, "mode": "default", "name": "my_sensor", "pipeline_name": "my_pipeline", "solid_selection": null}'
    external_sensor_data = deserialize_json_to_dagster_namedtuple(SERIALIZED_0_12_10_SENSOR)
    assert isinstance(external_sensor_data, ExternalSensorData)
    assert len(external_sensor_data.target_dict) == 1
    assert "my_pipeline" in external_sensor_data.target_dict
    target = external_sensor_data.target_dict["my_pipeline"]
    assert isinstance(target, ExternalTargetData)
    assert target.pipeline_name == "my_pipeline"
