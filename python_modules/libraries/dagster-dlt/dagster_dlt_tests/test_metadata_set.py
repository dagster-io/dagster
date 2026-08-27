import dlt
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue, TextMetadataValue
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
    # resolves a resource name and write disposition, so those are always present.
    assert set(metadata) == {"dagster-dlt/write_disposition", "dagster-dlt/resource"}
    assert metadata["dagster-dlt/write_disposition"] == TextMetadataValue("append")
    assert metadata["dagster-dlt/resource"] == "repos"


def test_round_trip_extract() -> None:
    @dlt.resource(name="repos", write_disposition="merge")
    def repos():
        yield {}

    metadata_set = DagsterDltMetadataSet.from_resource(repos)
    assert DagsterDltMetadataSet.extract(dict(metadata_set)) == metadata_set
