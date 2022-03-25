from pathlib import Path

import pytest

from dagster import (
    AssetMaterialization,
    AssetObservation,
    DagsterEventType,
    FloatMetadataValue,
    IntMetadataValue,
    MetadataValue,
    PathMetadataValue,
    PythonArtifactMetadataValue,
    TextMetadataValue,
    UrlMetadataValue,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.check import CheckError
from dagster.core.definitions.metadata import (
    DagsterInvalidMetadata,
    MetadataEntry,
    normalize_metadata,
)
from dagster.core.definitions.metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableRecord,
    TableSchema,
)
from dagster.utils import frozendict


def solid_events_for_type(result, solid_name, event_type):
    solid_result = result.result_for_solid(solid_name)
    return [
        compute_step_event
        for compute_step_event in solid_result.compute_step_events
        if compute_step_event.event_type == event_type
    ]


def test_metadata_entry_construction():
    entry_1 = MetadataEntry("foo", value=MetadataValue.text("bar"))
    entry_2 = MetadataEntry("foo", entry_data=MetadataValue.text("bar"))
    assert entry_1.value == MetadataValue.text("bar")
    assert entry_2.value == MetadataValue.text("bar")
    assert entry_1 == entry_2


def test_metadata_asset_materialization():
    @solid(output_defs=[])
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
    entry_map = {
        entry.label: entry.entry_data.__class__ for entry in materialization.metadata_entries
    }
    assert entry_map["text"] == TextMetadataValue
    assert entry_map["int"] == IntMetadataValue
    assert entry_map["url"] == UrlMetadataValue
    assert entry_map["float"] == FloatMetadataValue
    assert entry_map["path"] == PathMetadataValue
    assert entry_map["python"] == PythonArtifactMetadataValue


def test_metadata_asset_observation():
    @solid(output_defs=[])
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
    entry_map = {entry.label: entry.entry_data.__class__ for entry in observation.metadata_entries}
    assert entry_map["text"] == TextMetadataValue
    assert entry_map["int"] == IntMetadataValue
    assert entry_map["url"] == UrlMetadataValue
    assert entry_map["float"] == FloatMetadataValue
    assert entry_map["python"] == PythonArtifactMetadataValue


def test_unknown_metadata_value():
    @solid(output_defs=[])
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

    assert str(exc_info.value) == (
        'Could not resolve the metadata value for "bad" to a known type. '
        "Its type was <class 'dagster.core.instance.DagsterInstance'>. "
        "Consider wrapping the value with the appropriate MetadataValue type."
    )


def test_parse_invalid_metadata():

    metadata = {"foo": object()}

    with pytest.raises(DagsterInvalidMetadata) as _exc_info:
        normalize_metadata(metadata, [])

    entries = normalize_metadata(metadata, [], allow_invalid=True)
    assert len(entries) == 1
    assert entries[0].label == "foo"
    assert entries[0].entry_data == TextMetadataValue("[object] (unserializable)")


def test_parse_path_metadata():

    metadata = {"path": Path("/a/b.csv")}

    entries = normalize_metadata(metadata, [])
    assert len(entries) == 1
    assert entries[0].label == "path"
    assert entries[0].entry_data == PathMetadataValue("/a/b.csv")


def test_bad_json_metadata_value():
    @solid(output_defs=[])
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

    assert str(exc_info.value) == (
        'Could not resolve the metadata value for "bad" to a known type. '
        "Value is a dictionary but is not JSON serializable."
    )


def test_table_metadata_value_schema_inference():

    table_metadata_entry = MetadataEntry(
        "foo",
        value=MetadataValue.table(
            records=[
                TableRecord(name="foo", status=False),
                TableRecord(name="bar", status=True),
            ],
        ),
    )

    schema = table_metadata_entry.entry_data.schema  # type: ignore
    assert isinstance(schema, TableSchema)
    assert schema.columns == [
        TableColumn(name="name", type="string"),
        TableColumn(name="status", type="bool"),
    ]


bad_values = frozendict(
    {
        "table_schema": {"columns": False, "constraints": False},
        "table_column": {"name": False, "type": False, "description": False, "constraints": False},
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
        TableColumn(bad_key="foo", description="bar", type="string")  # type: ignore


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
        TableColumn(bad_key="foo")  # type: ignore


@pytest.mark.parametrize("key,value", list(bad_values["table_constraints"].items()))
def test_table_constraints(key, value):
    kwargs = {"other": ["foo"]}
    kwargs[key] = value
    with pytest.raises(CheckError):
        TableConstraints(**kwargs)


def test_table_column_constraints_keys():
    with pytest.raises(TypeError):
        TableColumnConstraints(bad_key="foo")  # type: ignore


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
        TableSchema(bad_key="foo")  # type: ignore


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
