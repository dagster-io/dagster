# This file strictly contains tests for deprecation warnings. It can serve as a central record of
# deprecations for the current version.

import re

import pytest

import dagster
from dagster._core.definitions.events import Output
from dagster._core.definitions.input import InputDefinition
from dagster._core.definitions.metadata import (
    DagsterAssetMetadataValue,
    DagsterRunMetadataValue,
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
from dagster._core.definitions.output import OutputDefinition
from dagster._core.types.dagster_type import DagsterType

# ########################
# ##### ASSET GROUP
# ########################


def test_asset_group_import():
    with pytest.warns(DeprecationWarning, match=re.escape("AssetGroup is deprecated")):
        getattr(dagster, "AssetGroup")


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
        "DagsterRunMetadataValue",
        DagsterRunMetadataValue,
    ),
    "DagsterPipelineRunMetadataValue": (
        "DagsterRunMetadataValue",
        DagsterRunMetadataValue,
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
        InputDefinition(name="foo", metadata={"foo": object()})


def test_metadata_entry_description():

    with pytest.warns(DeprecationWarning, match=re.escape('"description" attribute')):
        MetadataEntry("foo", "bar", MetadataValue.text("baz"))
