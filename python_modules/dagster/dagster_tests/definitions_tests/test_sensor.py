import pytest
from dagster import AssetKey, SensorDefinition, asset, graph
from dagster._core.errors import DagsterInvalidDefinitionError


def test_jobs_attr():
    def eval_fn():
        pass

    @graph
    def my_graph():
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, job=my_graph)
    assert sensor.job.name == my_graph.name

    sensor = SensorDefinition(evaluation_fn=eval_fn, job_name="my_pipeline")
    with pytest.raises(
        DagsterInvalidDefinitionError, match="No job was provided to SensorDefinition."
    ):
        sensor.job  # noqa: B018

    @graph
    def my_second_graph():
        pass

    sensor = SensorDefinition(evaluation_fn=eval_fn, jobs=[my_graph, my_second_graph])
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Job property not available when SensorDefinition has multiple jobs.",
    ):
        sensor.job  # noqa: B018


def test_direct_sensor_definition_instantiation():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Must provide evaluation_fn to SensorDefinition.",
    ):
        SensorDefinition()


def test_coerce_to_asset_selection():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    @asset
    def asset3():
        ...

    assets = [asset1, asset2, asset3]

    def evaluation_fn(context):
        raise NotImplementedError()

    assert SensorDefinition(
        "a", asset_selection=["asset1", "asset2"], evaluation_fn=evaluation_fn
    ).asset_selection.resolve(assets) == {AssetKey("asset1"), AssetKey("asset2")}

    sensor_def = SensorDefinition(
        "a", asset_selection=[asset1, asset2], evaluation_fn=evaluation_fn
    )
    assert sensor_def.asset_selection.resolve(assets) == {AssetKey("asset1"), AssetKey("asset2")}
