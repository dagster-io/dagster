from datetime import datetime
from pathlib import Path

import pendulum
import pytest
import pytz
from dagster import (
    AssetMaterialization,
    AssetObservation,
    BoolMetadataValue,
    DagsterEventType,
    FloatMetadataValue,
    IntMetadataValue,
    JsonMetadataValue,
    MetadataValue,
    NullMetadataValue,
    PathMetadataValue,
    PythonArtifactMetadataValue,
    TextMetadataValue,
    TimestampMetadataValue,
    UrlMetadataValue,
    job,
    op,
)
from dagster._check import CheckError
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata import (
    DagsterInvalidMetadata,
    TableMetadataValue,
    normalize_metadata,
)
from dagster._core.definitions.metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableRecord,
    TableSchema,
)
from dagster._core.execution.execution_result import ExecutionResult
from dagster._core.snap.node import build_node_defs_snapshot
from dagster._serdes.serdes import deserialize_value, serialize_value


def step_events_of_type(result: ExecutionResult, node_name: str, event_type: DagsterEventType):
    return [
        compute_step_event
        for compute_step_event in result.events_for_node(node_name)
        if compute_step_event.event_type == event_type
    ]


def test_metadata_asset_materialization():
    @op(out={})
    def the_op(_context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={
                "text": "FOO",
                "int": 22,
                "url": MetadataValue.url("http://fake.com"),
                "float": 0.1,
                "path": MetadataValue.path(Path("/a/b.csv")),
                "python": MetadataValue.python_artifact(MetadataValue),
                "timestamp": MetadataValue.timestamp(2000.5),
            },
        )

    @job
    def the_job():
        the_op()

    result = the_job.execute_in_process()

    assert result
    assert result.success

    materialization_events = step_events_of_type(
        result, "the_op", DagsterEventType.ASSET_MATERIALIZATION
    )
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization
    assert len(materialization.metadata) == 7
    entry_map = {k: v.__class__ for k, v in materialization.metadata.items()}
    assert entry_map["text"] == TextMetadataValue
    assert entry_map["int"] == IntMetadataValue
    assert entry_map["url"] == UrlMetadataValue
    assert entry_map["float"] == FloatMetadataValue
    assert entry_map["path"] == PathMetadataValue
    assert entry_map["python"] == PythonArtifactMetadataValue
    assert entry_map["timestamp"] == TimestampMetadataValue


def test_metadata_asset_observation():
    @op(out={})
    def the_op(_context):
        yield AssetObservation(
            asset_key="foo",
            metadata={
                "text": "FOO",
                "int": 22,
                "url": MetadataValue.url("http://fake.com"),
                "float": 0.1,
                "python": MetadataValue.python_artifact(MetadataValue),
            },
        )

    @job
    def the_job():
        the_op()

    result = the_job.execute_in_process()

    assert result
    assert result.success

    observation_events = step_events_of_type(result, "the_op", DagsterEventType.ASSET_OBSERVATION)
    assert len(observation_events) == 1
    observation = observation_events[0].event_specific_data.asset_observation
    assert len(observation.metadata) == 5
    entry_map = {k: v.__class__ for k, v in observation.metadata.items()}
    assert entry_map["text"] == TextMetadataValue
    assert entry_map["int"] == IntMetadataValue
    assert entry_map["url"] == UrlMetadataValue
    assert entry_map["float"] == FloatMetadataValue
    assert entry_map["python"] == PythonArtifactMetadataValue


def test_metadata_value_timestamp():
    pendulum_dt_with_timezone = pendulum.datetime(2024, 3, 6, 12, 0, 0, tz="America/New_York")
    assert (
        MetadataValue.timestamp(pendulum_dt_with_timezone).value
        == pendulum_dt_with_timezone.timestamp()
    )
    pendulum_dt_without_timezone = pendulum.datetime(2024, 3, 6, 12, 0, 0)
    assert (
        MetadataValue.timestamp(pendulum_dt_without_timezone).value
        == pendulum_dt_without_timezone.timestamp()
    )

    normal_dt_with_timezone = pytz.timezone("America/New_York").localize(
        datetime(2024, 3, 6, 12, 0, 0)
    )
    metadata_value = MetadataValue.timestamp(normal_dt_with_timezone)
    assert metadata_value.value == normal_dt_with_timezone.timestamp()
    assert metadata_value.value == pendulum_dt_with_timezone.timestamp()

    normal_dt_without_timezone = datetime(2024, 3, 6, 12, 0, 0)
    with pytest.raises(
        CheckError, match="Datetime values provided to MetadataValue.timestamp must have timezones"
    ):
        MetadataValue.timestamp(normal_dt_without_timezone)


def test_unknown_metadata_value():
    @op(out={})
    def the_op(context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={"bad": context.instance},
        )

    @job
    def the_job():
        the_op()

    with pytest.raises(DagsterInvalidMetadata) as exc_info:
        the_job.execute_in_process()

    assert (
        str(exc_info.value) == 'Could not resolve the metadata value for "bad" to a known type. '
        "Its type was <class 'dagster._core.instance.DagsterInstance'>. "
        "Consider wrapping the value with the appropriate MetadataValue type."
    )


def test_parse_null_metadata():
    metadata = {"foo": None}
    normalized = normalize_metadata(metadata)
    assert normalized["foo"] == NullMetadataValue()


def test_parse_list_metadata():
    metadata = {"foo": ["bar"]}
    normalized = normalize_metadata(metadata)
    assert normalized["foo"] == JsonMetadataValue(["bar"])


def test_parse_invalid_metadata():
    metadata = {"foo": object()}

    with pytest.raises(DagsterInvalidMetadata) as _exc_info:
        normalize_metadata(metadata)

    normalized = normalize_metadata(metadata, allow_invalid=True)
    assert normalized["foo"] == TextMetadataValue("[object] (unserializable)")


def test_parse_path_metadata():
    metadata = {"path": Path("/a/b.csv")}
    normalized = normalize_metadata(metadata)
    assert normalized["path"] == PathMetadataValue("/a/b.csv")


def test_bad_json_metadata_value():
    @op(out={})
    def the_op(context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={"bad": {"nested": context.instance}},
        )

    @job
    def the_job():
        the_op()

    with pytest.raises(DagsterInvalidMetadata) as exc_info:
        the_job.execute_in_process()

    assert (
        str(exc_info.value) == 'Could not resolve the metadata value for "bad" to a known type. '
        "Value is not JSON serializable."
    )


def test_table_metadata_value_schema_inference():
    table = MetadataValue.table(
        records=[
            TableRecord(data=dict(name="foo", status=False)),
            TableRecord(data=dict(name="bar", status=True)),
        ],
    )

    schema = table.schema
    assert isinstance(schema, TableSchema)
    assert schema.columns == [
        TableColumn(name="name", type="string"),
        TableColumn(name="status", type="bool"),
    ]


bad_values = {
    "table_schema": {"columns": False, "constraints": False},
    "table_column": {
        "name": False,
        "type": False,
        "description": False,
        "constraints": False,
    },
    "table_constraints": {"other": False},
    "table_column_constraints": {
        "nullable": "foo",
        "unique": "foo",
        "other": False,
    },
}


def test_table_column_keys():
    with pytest.raises(TypeError):
        TableColumn(bad_key="foo", description="bar", type="string")


@pytest.mark.parametrize("key,value", list(bad_values["table_column"].items()))
def test_table_column_values(key, value):
    kwargs = {
        "name": "foo",
        "type": "string",
        "description": "bar",
        "constraints": TableColumnConstraints(other=["foo"]),
    }
    kwargs[key] = value
    with pytest.raises(CheckError):
        TableColumn(**kwargs)


def test_table_constraints_keys():
    with pytest.raises(TypeError):
        TableColumn(bad_key="foo")


@pytest.mark.parametrize("key,value", list(bad_values["table_constraints"].items()))
def test_table_constraints(key, value):
    kwargs = {"other": ["foo"]}
    kwargs[key] = value
    with pytest.raises(CheckError):
        TableConstraints(**kwargs)


def test_table_column_constraints_keys():
    with pytest.raises(TypeError):
        TableColumnConstraints(bad_key="foo")


# minimum and maximum aren't checked because they depend on the type of the column
@pytest.mark.parametrize("key,value", list(bad_values["table_column_constraints"].items()))
def test_table_column_constraints_values(key, value):
    kwargs = {
        "nullable": True,
        "unique": True,
        "other": ["foo"],
    }
    kwargs[key] = value
    with pytest.raises(CheckError):
        TableColumnConstraints(**kwargs)


def test_table_schema_keys():
    with pytest.raises(TypeError):
        TableSchema(bad_key="foo")


@pytest.mark.parametrize("key,value", list(bad_values["table_schema"].items()))
def test_table_schema_values(key, value):
    kwargs = {
        "constraints": TableConstraints(other=["foo"]),
        "columns": [
            TableColumn(
                name="foo",
                type="string",
                description="bar",
                constraints=TableColumnConstraints(other=["foo"]),
            )
        ],
    }
    kwargs[key] = value
    with pytest.raises(CheckError):
        TableSchema(**kwargs)


def test_complex_table_schema():
    assert isinstance(
        TableSchema(
            columns=[
                TableColumn(
                    name="foo",
                    type="customtype",
                    constraints=TableColumnConstraints(
                        nullable=True,
                        unique=True,
                    ),
                ),
                TableColumn(
                    name="bar",
                    type="string",
                    description="bar",
                    constraints=TableColumnConstraints(
                        nullable=False,
                        other=["foo"],
                    ),
                ),
            ],
            constraints=TableConstraints(other=["foo"]),
        ),
        TableSchema,
    )


def test_table_schema_from_name_type_dict():
    assert TableSchema.from_name_type_dict({"foo": "customtype", "bar": "string"}) == TableSchema(
        columns=[
            TableColumn(name="foo", type="customtype"),
            TableColumn(name="bar", type="string"),
        ],
    )


def test_table_serialization():
    table_metadata = MetadataValue.table(
        records=[
            TableRecord(dict(foo=1, bar=2)),
        ],
    )
    serialized = serialize_value(table_metadata)
    assert deserialize_value(serialized, TableMetadataValue) == table_metadata


def test_bool_metadata_value():
    @op(out={})
    def the_op():
        yield AssetMaterialization(
            asset_key="foo",
            metadata={"first_bool": True, "second_bool": BoolMetadataValue(False)},
        )

    @job
    def the_job():
        the_op()

    result = the_job.execute_in_process()

    assert result
    assert result.success

    materialization_events = step_events_of_type(
        result, "the_op", DagsterEventType.ASSET_MATERIALIZATION
    )
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization
    entry_map = {k: v.__class__ for k, v in materialization.metadata.items()}
    assert entry_map["first_bool"] == BoolMetadataValue
    assert entry_map["second_bool"] == BoolMetadataValue


def test_snapshot_arbitrary_metadata():
    # Asset decorator accepts arbitrary metadata. Need to ensure this doesn't throw an error when a
    # snap is created.
    @asset(metadata={"my_key": [object()]})
    def foo_asset():
        pass

    assert build_node_defs_snapshot(
        Definitions(assets=[foo_asset]).get_implicit_global_asset_job_def()
    )
