# This file strictly contains tests for deprecation warnings. It can serve as a central record of
# deprecations for the current version.

import dagster
import pytest
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


def test_deprecated_metadata_classes(metadata_entry_class_name):
    with pytest.warns(DeprecationWarning):
        assert (
            getattr(dagster, metadata_entry_class_name)
            == METADATA_DEPRECATIONS[metadata_entry_class_name][1]
        )
