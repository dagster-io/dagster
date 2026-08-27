from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue, TextMetadataValue
from dagster_dlt.metadata_set import DagsterDltMetadataSet


def test_namespace() -> None:
    assert DagsterDltMetadataSet.namespace() == "dagster-dlt"


def test_from_table_schema_string_values() -> None:
    metadata = dict(
        DagsterDltMetadataSet.from_table_schema(
            {
                "name": "repos",
                "resource": "repos",
                "write_disposition": "merge",
                "table_format": "iceberg",
                "file_format": "parquet",
            }
        )
    )

    assert metadata["dagster-dlt/write_disposition"] == TextMetadataValue("merge")
    # ``resource``/``table_format``/``file_format`` are plain string fields
    assert metadata["dagster-dlt/resource"] == "repos"
    assert metadata["dagster-dlt/table_format"] == "iceberg"
    assert metadata["dagster-dlt/file_format"] == "parquet"


def test_from_table_schema_dict_schema_contract() -> None:
    metadata = dict(
        DagsterDltMetadataSet.from_table_schema(
            {"name": "repos", "schema_contract": {"tables": "evolve", "columns": "freeze"}}
        )
    )

    assert metadata["dagster-dlt/schema_contract"] == JsonMetadataValue(
        {"tables": "evolve", "columns": "freeze"}
    )


def test_from_table_schema_string_schema_contract() -> None:
    metadata = dict(
        DagsterDltMetadataSet.from_table_schema({"name": "repos", "schema_contract": "freeze"})
    )

    assert metadata["dagster-dlt/schema_contract"] == TextMetadataValue("freeze")


def test_from_table_schema_omits_absent_values() -> None:
    metadata = dict(
        DagsterDltMetadataSet.from_table_schema({"name": "repos", "write_disposition": "append"})
    )

    # Only the populated key is present; unset fields are omitted entirely.
    assert set(metadata) == {"dagster-dlt/write_disposition"}
    assert metadata["dagster-dlt/write_disposition"] == TextMetadataValue("append")


def test_round_trip_extract() -> None:
    metadata_set = DagsterDltMetadataSet.from_table_schema(
        {"name": "repos", "resource": "repos", "write_disposition": "merge"}
    )
    assert DagsterDltMetadataSet.extract(dict(metadata_set)) == metadata_set
