import dlt
from dagster._core.definitions.metadata.metadata_value import (
    JsonMetadataValue,
    MetadataValue,
    TextMetadataValue,
)
from dagster_dlt.metadata_set import DagsterDltMetadataSet


def test_namespace() -> None:
    assert DagsterDltMetadataSet.namespace() == "dagster-dlt"


def test_from_resource_string_values() -> None:
    @dlt.resource(name="repos", write_disposition="merge", table_format="iceberg")
    def repos():
        yield {}

    metadata = dict(DagsterDltMetadataSet.from_resource(repos))

    assert metadata["dagster-dlt/write_disposition"] == TextMetadataValue("merge")
    # ``resource``/``table_format`` are plain string fields
    assert metadata["dagster-dlt/resource"] == "repos"
    assert metadata["dagster-dlt/table_format"] == "iceberg"


def test_from_resource_dict_schema_contract() -> None:
    @dlt.resource(name="repos", schema_contract={"tables": "evolve", "columns": "freeze"})
    def repos():
        yield {}

    metadata = dict(DagsterDltMetadataSet.from_resource(repos))

    assert metadata["dagster-dlt/schema_contract"] == JsonMetadataValue(
        {"tables": "evolve", "columns": "freeze"}
    )


def test_from_resource_string_schema_contract() -> None:
    @dlt.resource(name="repos", schema_contract="freeze")
    def repos():
        yield {}

    metadata = dict(DagsterDltMetadataSet.from_resource(repos))

    assert metadata["dagster-dlt/schema_contract"] == TextMetadataValue("freeze")


def test_from_resource_omits_absent_values() -> None:
    @dlt.resource(name="repos", write_disposition="append")
    def repos():
        yield {}

    metadata = dict(DagsterDltMetadataSet.from_resource(repos))

    # Unset optional hints (schema_contract, table_format) are omitted entirely. dlt always
    # resolves a resource name, table name, and write disposition, so those are always present.
    assert set(metadata) == {
        "dagster-dlt/write_disposition",
        "dagster-dlt/resource",
        "dagster-dlt/table_name",
    }
    assert metadata["dagster-dlt/write_disposition"] == TextMetadataValue("append")
    assert metadata["dagster-dlt/resource"] == "repos"
    assert metadata["dagster-dlt/table_name"] == "repos"


def test_from_pipeline() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="test_pipeline", dataset_name="my_dataset", destination="duckdb"
    )

    metadata = dict(DagsterDltMetadataSet.from_pipeline(pipeline))

    assert metadata["dagster-dlt/destination_name"] == "duckdb"
    assert metadata["dagster-dlt/destination_type"] == "dlt.destinations.duckdb"
    assert metadata["dagster-dlt/dataset_name"] == "my_dataset"
    # Resource-only hints are not populated when building from the pipeline.
    assert "dagster-dlt/resource" not in metadata
    assert "dagster-dlt/table_name" not in metadata


def test_runtime_fields() -> None:
    metadata_set = DagsterDltMetadataSet(
        first_run=True,
        started_at="2026-08-27T00:00:00Z",
        finished_at="2026-08-27T00:01:00Z",
        rows_loaded=0,
        jobs=MetadataValue.json([{"table_name": "repos"}]),
    )
    metadata = dict(metadata_set)

    # ``rows_loaded`` of 0 is still emitted (it is not None).
    assert metadata["dagster-dlt/rows_loaded"] == 0
    assert metadata["dagster-dlt/first_run"] is True
    assert metadata["dagster-dlt/jobs"] == JsonMetadataValue([{"table_name": "repos"}])
    assert DagsterDltMetadataSet.extract(metadata) == metadata_set


def test_round_trip_extract() -> None:
    @dlt.resource(name="repos", write_disposition="merge")
    def repos():
        yield {}

    metadata_set = DagsterDltMetadataSet.from_resource(repos)
    assert DagsterDltMetadataSet.extract(dict(metadata_set)) == metadata_set
