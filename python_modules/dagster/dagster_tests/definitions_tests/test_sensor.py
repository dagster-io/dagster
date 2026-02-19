import dagster as dg
import pytest
from dagster._core.definitions.sensor_definition import SensorType


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
            dg.DagsterInvalidDefinitionError, match=r"No job was provided to SensorDefinition."
        ):
            getattr(sensor, attr)

    @dg.graph
    def my_second_graph():
        pass

    sensor = dg.SensorDefinition(evaluation_fn=eval_fn, jobs=[my_graph, my_second_graph])
    for attr in ["job", "job_name"]:
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match=r"property not available when SensorDefinition has multiple jobs.",
        ):
            getattr(sensor, attr)


def test_direct_sensor_definition_instantiation():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Must provide evaluation_fn to SensorDefinition.",
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
        my_sensor = dg.SensorDefinition(job=bar, evaluation_fn=lambda _: None)

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


def test_sensor_metadata_preserved_through_with_definition_metadata_update():
    """Test that sensor_type and other attributes are preserved when metadata is updated via Definitions."""

    # Create a dummy job for sensors that need it
    @dg.job
    def my_job():
        pass

    # Test AutomationConditionSensorDefinition
    automation_sensor = dg.AutomationConditionSensorDefinition(
        name="test_automation_sensor",
        target="group:test",
    )
    assert automation_sensor.sensor_type == SensorType.AUTO_MATERIALIZE

    defs = dg.Definitions(sensors=[automation_sensor]).with_definition_metadata_update(
        lambda metadata: {**metadata, "foo": "bar"}
    )

    updated_automation_sensor = defs.get_sensor_def("test_automation_sensor")
    assert updated_automation_sensor.metadata["foo"].value == "bar"
    assert updated_automation_sensor.sensor_type == SensorType.AUTO_MATERIALIZE

    # Test RunStatusSensorDefinition
    @dg.run_status_sensor(run_status=dg.DagsterRunStatus.SUCCESS, name="test_run_status_sensor")
    def my_run_status_sensor(context):
        pass

    assert my_run_status_sensor.sensor_type == SensorType.RUN_STATUS

    defs = dg.Definitions(
        sensors=[my_run_status_sensor], jobs=[my_job]
    ).with_definition_metadata_update(lambda metadata: {**metadata, "baz": "qux"})

    updated_run_status_sensor = defs.get_sensor_def("test_run_status_sensor")
    assert updated_run_status_sensor.metadata["baz"].value == "qux"
    assert updated_run_status_sensor.sensor_type == SensorType.RUN_STATUS

    # Test AssetSensorDefinition
    @dg.asset_sensor(asset_key=dg.AssetKey("my_asset"), job_name="my_job")
    def my_asset_sensor(context, asset_event):
        pass

    assert my_asset_sensor.sensor_type == SensorType.ASSET

    defs = dg.Definitions(sensors=[my_asset_sensor], jobs=[my_job]).with_definition_metadata_update(
        lambda metadata: {**metadata, "asset_metadata": "value"}
    )

    updated_asset_sensor = defs.get_sensor_def("my_asset_sensor")
    assert updated_asset_sensor.metadata["asset_metadata"].value == "value"
    assert updated_asset_sensor.sensor_type == SensorType.ASSET

    # Test MultiAssetSensorDefinition
    @dg.multi_asset_sensor(
        monitored_assets=[dg.AssetKey("asset1"), dg.AssetKey("asset2")],
        name="test_multi_asset_sensor",
        job_name="my_job",
    )
    def my_multi_asset_sensor(context):
        pass

    assert my_multi_asset_sensor.sensor_type == SensorType.MULTI_ASSET

    defs = dg.Definitions(
        sensors=[my_multi_asset_sensor], jobs=[my_job]
    ).with_definition_metadata_update(lambda metadata: {**metadata, "multi": "metadata"})

    updated_multi_asset_sensor = defs.get_sensor_def("test_multi_asset_sensor")
    assert updated_multi_asset_sensor.metadata["multi"].value == "metadata"
    assert updated_multi_asset_sensor.sensor_type == SensorType.MULTI_ASSET

    # Test base SensorDefinition
    @dg.sensor(name="test_base_sensor", job_name="my_job")
    def my_base_sensor(context):
        pass

    assert my_base_sensor.sensor_type == SensorType.STANDARD

    defs = dg.Definitions(sensors=[my_base_sensor], jobs=[my_job]).with_definition_metadata_update(
        lambda metadata: {**metadata, "standard": "sensor"}
    )

    updated_base_sensor = defs.get_sensor_def("test_base_sensor")
    assert updated_base_sensor.metadata["standard"].value == "sensor"
    assert updated_base_sensor.sensor_type == SensorType.STANDARD
