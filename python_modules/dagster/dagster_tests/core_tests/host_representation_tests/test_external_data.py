from typing import Dict

import pytest
from dagster import AssetKey, DagsterInvariantViolationError, In, Out, job, pipeline
from dagster.core.asset_defs import ForeignAsset
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


def asset(fn):
    asset_name = fn.__name__

    ins: Dict[str, In] = {}
    for input_param in get_function_params(fn):
        input_param_name = input_param.name
        asset_key = AssetKey(input_param_name)
        ins[input_param_name] = In(asset_key=asset_key)

    out = Out(asset_key=AssetKey(asset_name))
    return _Op(
        name=asset_name,
        ins=ins,
        out=out,
    )(fn)


def test_single_asset_pipeline():
    @asset
    def asset1():
        return 1

    @pipeline
    def my_graph():
        asset1()

    external_asset_nodes = external_asset_graph_from_defs([my_graph], foreign_assets_by_key={})

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[],
            op_name="asset1",
            op_description=None,
            job_names=["my_graph"],
        )
    ]


def test_two_asset_pipeline():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    @pipeline
    def my_graph():
        asset2(asset1())

    external_asset_nodes = external_asset_graph_from_defs([my_graph], foreign_assets_by_key={})

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
            job_names=["my_graph"],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=["my_graph"],
        ),
    ]


def test_cross_pipeline_asset_dependency():
    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        assert asset1 == 1

    @pipeline
    def asset1_graph():
        asset1()

    @pipeline
    def asset2_graph():
        asset2()  # pylint: disable=no-value-for-parameter

    external_asset_nodes = external_asset_graph_from_defs(
        [asset1_graph, asset2_graph], foreign_assets_by_key={}
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
            job_names=["asset1_graph"],
        ),
        ExternalAssetNode(
            asset_key=AssetKey("asset2"),
            dependencies=[
                ExternalAssetDependency(upstream_asset_key=AssetKey("asset1"), input_name="asset1")
            ],
            depended_by=[],
            op_name="asset2",
            op_description=None,
            job_names=["asset2_graph"],
        ),
    ]


def test_same_asset_in_multiple_pipelines():
    @asset
    def asset1():
        return 1

    @pipeline
    def graph1():
        asset1()

    @pipeline
    def graph2():
        asset1()

    external_asset_nodes = external_asset_graph_from_defs(
        [graph1, graph2], foreign_assets_by_key={}
    )

    assert external_asset_nodes == [
        ExternalAssetNode(
            asset_key=AssetKey("asset1"),
            dependencies=[],
            depended_by=[],
            op_name="asset1",
            op_description=None,
            job_names=["graph1", "graph2"],
        ),
    ]


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

    @job
    def job1():
        foo()  # pylint: disable=no-value-for-parameter

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
        ),
    ]


def test_foreign_asset_conflicts_with_asset():
    bar_foreign_asset = ForeignAsset(key=AssetKey("bar"), description="def")

    @asset
    def bar():
        pass

    @job
    def job1():
        bar()  # pylint: disable=no-value-for-parameter

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
