# This file strictly contains tests for deprecation warnings. It can serve as a central record of
# deprecations for the current version.

import re

import pytest

import dagster
from dagster.core.definitions.events import Output
from dagster.core.definitions.input import InputDefinition
from dagster.core.definitions.metadata import (
    DagsterAssetMetadataValue,
    DagsterPipelineRunMetadataValue,
    FloatMetadataValue,
    IntMetadataValue,
    JsonMetadataValue,
    MarkdownMetadataValue,
    MetadataEntry,
    MetadataValue,
    PathMetadataValue,
    PythonArtifactMetadataValue,
    TableMetadataValue,
    TableSchemaMetadataValue,
    TextMetadataValue,
    UrlMetadataValue,
)
from dagster.core.definitions.output import OutputDefinition
from dagster.core.types.dagster_type import DagsterType

# ########################
# ##### METADATA IMPORTS
# ########################


METADATA_DEPRECATIONS = {
    "EventMetadataEntry": ("MetadataEntry", MetadataEntry),
    "EventMetadata": ("MetadataValue", MetadataValue),
    "TextMetadataEntryData": ("TextMetadataValue", TextMetadataValue),
    "UrlMetadataEntryData": ("UrlMetadataValue", UrlMetadataValue),
    "PathMetadataEntryData": ("PathMetadataValue", PathMetadataValue),
    "JsonMetadataEntryData": ("JsonMetadataValue", JsonMetadataValue),
    "MarkdownMetadataEntryData": ("MarkdownMetadataValue", MarkdownMetadataValue),
    "PythonArtifactMetadataEntryData": ("PythonArtifactMetadataValue", PythonArtifactMetadataValue),
    "FloatMetadataEntryData": ("FloatMetadataValue", FloatMetadataValue),
    "IntMetadataEntryData": ("IntMetadataValue", IntMetadataValue),
    "DagsterPipelineRunMetadataEntryData": (
        "DagsterPipelineRunMetadataValue",
        DagsterPipelineRunMetadataValue,
    ),
    "DagsterAssetMetadataEntryData": ("DagsterAssetMetadataValue", DagsterAssetMetadataValue),
    "TableMetadataEntryData": ("TableMetadataValue", TableMetadataValue),
    "TableSchemaMetadataEntryData": ("TableSchemaMetadataValue", TableSchemaMetadataValue),
}


@pytest.fixture(params=METADATA_DEPRECATIONS.keys())
def metadata_entry_class_name(request):
    return request.param


def test_metadata_classes(metadata_entry_class_name):
    assert (
        getattr(dagster, metadata_entry_class_name)
        == METADATA_DEPRECATIONS[metadata_entry_class_name][1]
    )


# ########################
# ##### METADATA ARGUMENTS
# ########################


def test_metadata_entries():

    metadata_entry = MetadataEntry("foo", None, MetadataValue.text("bar"))

    # We use `Output` as a stand-in for all events here, they all follow the same pattern of calling
    # `normalize_metadata`.
    with pytest.warns(DeprecationWarning, match=re.escape('"metadata_entries" is deprecated')):
        Output("foo", "bar", metadata_entries=[metadata_entry])

    with pytest.warns(DeprecationWarning, match=re.escape('"metadata_entries" is deprecated')):
        DagsterType(lambda _, __: True, "foo", metadata_entries=[metadata_entry])


def test_arbitrary_metadata():

    with pytest.warns(DeprecationWarning, match=re.escape("arbitrary metadata values")):
        OutputDefinition(metadata={"foo": object()})

    with pytest.warns(DeprecationWarning, match=re.escape("arbitrary metadata values")):
        InputDefinition(metadata={"foo": object()})


def test_metadata_entry_description():

    with pytest.warns(DeprecationWarning, match=re.escape('"description" attribute')):
        MetadataEntry("foo", "bar", MetadataValue.text("baz"))
