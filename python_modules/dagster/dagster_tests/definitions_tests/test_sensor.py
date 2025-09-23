import dagster as dg
import pytest


def test_jobs_attr():
    def eval_fn():
        pass

    @dg.graph
    def my_graph():
        pass

    sensor = dg.SensorDefinition(evaluation_fn=eval_fn, job=my_graph)
    assert sensor.job.name == my_graph.name
    assert sensor.job_name == my_graph.name

    sensor = dg.SensorDefinition(evaluation_fn=eval_fn, asset_selection=["foo"])
    for attr in ["job", "job_name"]:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError, match="No job was provided to SensorDefinition."
        ):
            getattr(sensor, attr)

    @dg.graph
    def my_second_graph():
        pass

    sensor = dg.SensorDefinition(evaluation_fn=eval_fn, jobs=[my_graph, my_second_graph])
    for attr in ["job", "job_name"]:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match="property not available when SensorDefinition has multiple jobs.",
        ):
            getattr(sensor, attr)


def test_direct_sensor_definition_instantiation():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Must provide evaluation_fn to SensorDefinition.",
    ):
        dg.SensorDefinition()


def test_coerce_to_asset_selection():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    @dg.asset
    def asset3(): ...

    assets = [asset1, asset2, asset3]

    def evaluation_fn(context):
        raise NotImplementedError()

    assert dg.SensorDefinition(
        "a", asset_selection=["asset1", "asset2"], evaluation_fn=evaluation_fn
    ).asset_selection.resolve(assets) == {dg.AssetKey("asset1"), dg.AssetKey("asset2")}  # pyright: ignore[reportOptionalMemberAccess]

    sensor_def = dg.SensorDefinition(
        "a", asset_selection=[asset1, asset2], evaluation_fn=evaluation_fn
    )
    assert sensor_def.asset_selection.resolve(assets) == {  # pyright: ignore[reportOptionalMemberAccess]
        dg.AssetKey("asset1"),
        dg.AssetKey("asset2"),
    }


def test_coerce_graph_def_to_job():
    @dg.op
    def foo(): ...

    @dg.graph
    def bar():
        foo()

    with pytest.warns(DeprecationWarning, match="Passing GraphDefinition"):
        my_sensor = dg.SensorDefinition(job=bar, evaluation_fn=lambda _: ...)

    assert isinstance(my_sensor.job, dg.JobDefinition)
    assert my_sensor.job.name == "bar"


def test_with_attributes():
    @dg.job
    def one(): ...

    @dg.job
    def two(): ...

    def fn(): ...

    sensor = dg.SensorDefinition(job=one, metadata={"foo": "bar", "four": 4}, evaluation_fn=fn)

    blanked = sensor.with_attributes(metadata={})
    assert blanked.metadata == {}

    sensor = dg.SensorDefinition(
        jobs=[one, two], metadata={"foo": "bar", "four": 4}, evaluation_fn=fn
    )
    updated = sensor.with_attributes(metadata={**sensor.metadata, "foo": "baz"})

    assert updated.metadata["foo"] == dg.TextMetadataValue("baz")
    assert updated.metadata["four"] == dg.IntMetadataValue(4)

    name_sensor = dg.SensorDefinition(job_name="foo", evaluation_fn=fn)
    updated_name_sensor = name_sensor.with_attributes(metadata={"foo": "bar"})
    assert updated_name_sensor.metadata["foo"] == dg.TextMetadataValue("bar")

    assert updated_name_sensor.targets == name_sensor.targets

    empty_sensor = dg.SensorDefinition(evaluation_fn=fn)
    updated_empty_sensor = empty_sensor.with_attributes(metadata={"foo": "bar"})
    assert updated_empty_sensor.metadata["foo"] == dg.TextMetadataValue("bar")
    assert updated_empty_sensor.targets == empty_sensor.targets


def test_owners():
    def eval_fn():
        pass

    sensor = dg.SensorDefinition(
        evaluation_fn=eval_fn, job_name="test_job", owners=["user@example.com", "team:data"]
    )
    assert sensor.owners == ["user@example.com", "team:data"]


def test_owners_validation():
    def eval_fn():
        pass

    # Test invalid team name with special characters
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="contains invalid characters"):
        dg.SensorDefinition(evaluation_fn=eval_fn, job_name="test_job", owners=["team:bad-name"])

    # Test empty team name
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Team name cannot be empty"):
        dg.SensorDefinition(evaluation_fn=eval_fn, job_name="test_job", owners=["team:"])
