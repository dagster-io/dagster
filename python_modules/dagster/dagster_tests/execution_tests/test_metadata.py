from pathlib import Path

import pytest
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
    UrlMetadataValue,
)
from dagster._check import CheckError
from dagster._core.definitions.decorators import op
from dagster._core.definitions.metadata import (
    DagsterInvalidMetadata,
    MetadataEntry,
    normalize_metadata,
)
from dagster._core.definitions.metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableRecord,
    TableSchema,
)
from dagster._core.execution.results import OpExecutionResult, PipelineExecutionResult
from dagster._legacy import execute_pipeline, pipeline
from dagster._serdes.serdes import deserialize_value, serialize_value
from dagster._utils import frozendict


def solid_events_for_type(
    result: PipelineExecutionResult, solid_name: str, event_type: DagsterEventType
):
    solid_result = result.result_for_node(solid_name)
    assert isinstance(solid_result, OpExecutionResult)
    return [
        compute_step_event
        for compute_step_event in solid_result.compute_step_events
        if compute_step_event.event_type == event_type
    ]


def test_metadata_entry_construction():
    entry = MetadataEntry("foo", value=MetadataValue.text("bar"))
    assert entry.label == "foo"
    assert entry.value == MetadataValue.text("bar")


def test_metadata_asset_materialization():
    @op(out={})
    def the_solid(_context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={
                "text": "FOO",
                "int": 22,
                "url": MetadataValue.url("http://fake.com"),
                "float": 0.1,
                "path": MetadataValue.path(Path("/a/b.csv")),
                "python": MetadataValue.python_artifact(MetadataValue),
            },
        )

    @pipeline
    def the_pipeline():
        the_solid()

    result = execute_pipeline(the_pipeline)

    assert result
    assert result.success

    materialization_events = solid_events_for_type(
        result, "the_solid", DagsterEventType.ASSET_MATERIALIZATION
    )
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization
    assert len(materialization.metadata_entries) == 6
    entry_map = {entry.label: entry.value.__class__ for entry in materialization.metadata_entries}
    assert entry_map["text"] == TextMetadataValue
    assert entry_map["int"] == IntMetadataValue
    assert entry_map["url"] == UrlMetadataValue
    assert entry_map["float"] == FloatMetadataValue
    assert entry_map["path"] == PathMetadataValue
    assert entry_map["python"] == PythonArtifactMetadataValue


def test_metadata_asset_observation():
    @op(out={})
    def the_solid(_context):
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

    @pipeline
    def the_pipeline():
        the_solid()

    result = execute_pipeline(the_pipeline)

    assert result
    assert result.success

    observation_events = solid_events_for_type(
        result, "the_solid", DagsterEventType.ASSET_OBSERVATION
    )
    assert len(observation_events) == 1
    observation = observation_events[0].event_specific_data.asset_observation
    assert len(observation.metadata_entries) == 5
    entry_map = {entry.label: entry.value.__class__ for entry in observation.metadata_entries}
    assert entry_map["text"] == TextMetadataValue
    assert entry_map["int"] == IntMetadataValue
    assert entry_map["url"] == UrlMetadataValue
    assert entry_map["float"] == FloatMetadataValue
    assert entry_map["python"] == PythonArtifactMetadataValue


def test_unknown_metadata_value():
    @op
    def the_solid(context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={"bad": context.instance},
        )

    @pipeline
    def the_pipeline():
        the_solid()

    with pytest.raises(DagsterInvalidMetadata) as exc_info:
        execute_pipeline(the_pipeline)

    assert (
        str(exc_info.value)
        == 'Could not resolve the metadata value for "bad" to a known type. '
        "Its type was <class 'dagster._core.instance.DagsterInstance'>. "
        "Consider wrapping the value with the appropriate MetadataValue type."
    )


def test_parse_null_metadata():
    metadata = {"foo": None}
    entries = normalize_metadata(metadata, [])
    assert entries[0].label == "foo"
    assert entries[0].value == NullMetadataValue()


def test_parse_list_metadata():
    metadata = {"foo": ["bar"]}
    entries = normalize_metadata(metadata, [])
    assert entries[0].label == "foo"
    assert entries[0].value == JsonMetadataValue(["bar"])


def test_parse_invalid_metadata():
    metadata = {"foo": object()}

    with pytest.raises(DagsterInvalidMetadata) as _exc_info:
        normalize_metadata(metadata, [])

    entries = normalize_metadata(metadata, [], allow_invalid=True)
    assert len(entries) == 1
    assert entries[0].label == "foo"
    assert entries[0].value == TextMetadataValue("[object] (unserializable)")


def test_parse_path_metadata():
    metadata = {"path": Path("/a/b.csv")}

    entries = normalize_metadata(metadata, [])
    assert len(entries) == 1
    assert entries[0].label == "path"
    assert entries[0].value == PathMetadataValue("/a/b.csv")


def test_bad_json_metadata_value():
    @op
    def the_solid(context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={"bad": {"nested": context.instance}},
        )

    @pipeline
    def the_pipeline():
        the_solid()

    with pytest.raises(DagsterInvalidMetadata) as exc_info:
        execute_pipeline(the_pipeline)

    assert (
        str(exc_info.value)
        == 'Could not resolve the metadata value for "bad" to a known type. '
        "Value is not JSON serializable."
    )


def test_table_metadata_value_schema_inference():
    table_metadata_entry = MetadataEntry(
        "foo",
        value=MetadataValue.table(
            records=[
                TableRecord(data=dict(name="foo", status=False)),
                TableRecord(data=dict(name="bar", status=True)),
            ],
        ),
    )

    schema = table_metadata_entry.value.schema
    assert isinstance(schema, TableSchema)
    assert schema.columns == [
        TableColumn(name="name", type="string"),
        TableColumn(name="status", type="bool"),
    ]


bad_values = frozendict(
    {
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
)


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
    entry = MetadataEntry(
        "foo",
        value=MetadataValue.table(
            records=[
                TableRecord(dict(foo=1, bar=2)),
            ],
        ),
    )
    serialized = serialize_value(entry)
    assert deserialize_value(serialized, MetadataEntry) == entry


def test_bool_metadata_value():
    @op(out={})
    def the_solid():
        yield AssetMaterialization(
            asset_key="foo",
            metadata={"first_bool": True, "second_bool": BoolMetadataValue(False)},
        )

    @pipeline
    def the_pipeline():
        the_solid()

    result = execute_pipeline(the_pipeline)

    assert result
    assert result.success

    materialization_events = solid_events_for_type(
        result, "the_solid", DagsterEventType.ASSET_MATERIALIZATION
    )
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization
    entry_map = {entry.label: entry.value.__class__ for entry in materialization.metadata_entries}
    assert entry_map["first_bool"] == BoolMetadataValue
    assert entry_map["second_bool"] == BoolMetadataValue
