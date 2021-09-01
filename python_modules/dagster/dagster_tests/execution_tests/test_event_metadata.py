import pytest
from dagster import (
    AssetMaterialization,
    DagsterEventType,
    EventMetadata,
    FloatMetadataEntryData,
    IntMetadataEntryData,
    PythonArtifactMetadataEntryData,
    TextMetadataEntryData,
    UrlMetadataEntryData,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.core.definitions.event_metadata import DagsterInvalidEventMetadata


def solid_events_for_type(result, solid_name, event_type):
    solid_result = result.result_for_solid(solid_name)
    return [
        compute_step_event
        for compute_step_event in solid_result.compute_step_events
        if compute_step_event.event_type == event_type
    ]


def test_event_metadata():
    @solid(output_defs=[])
    def the_solid(_context):
        yield AssetMaterialization(
            asset_key="foo",
            metadata={
                "text": "FOO",
                "int": 22,
                "url": EventMetadata.url("http://fake.com"),
                "float": 0.1,
                "python": EventMetadata.python_artifact(EventMetadata),
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
    assert len(materialization.metadata_entries) == 5
    entry_map = {
        entry.label: entry.entry_data.__class__ for entry in materialization.metadata_entries
    }
    assert entry_map["text"] == TextMetadataEntryData
    assert entry_map["int"] == IntMetadataEntryData
    assert entry_map["url"] == UrlMetadataEntryData
    assert entry_map["float"] == FloatMetadataEntryData
    assert entry_map["python"] == PythonArtifactMetadataEntryData


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

    with pytest.raises(DagsterInvalidEventMetadata) as exc_info:
        execute_pipeline(the_pipeline)

    assert str(exc_info.value) == (
        'Could not resolve the metadata value for "bad" to a known type. '
        "Consider wrapping the value with the appropriate EventMetadata type."
    )


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

    with pytest.raises(DagsterInvalidEventMetadata) as exc_info:
        execute_pipeline(the_pipeline)

    assert str(exc_info.value) == (
        'Could not resolve the metadata value for "bad" to a JSON serializable value. '
        "Consider wrapping the value with the appropriate EventMetadata type."
    )
