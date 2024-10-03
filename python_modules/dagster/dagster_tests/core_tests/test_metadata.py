import pytest
from dagster import (
    AssetKey,
    GraphDefinition,
    IntMetadataValue,
    JsonMetadataValue,
    MetadataValue,
    NodeInvocation,
    TableColumn,
    TableColumnDep,
    TableColumnLineage,
    TableMetadataValue,
    TableRecord,
    TableSchema,
    TableSchemaMetadataValue,
    UrlMetadataValue,
    op,
)
from dagster._check.functions import CheckError
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
)
from dagster._serdes.serdes import deserialize_value, serialize_value


def test_op_instance_tags():
    called = {}

    @op(tags={"foo": "bar", "baz": "quux"})
    def metadata_op(context):
        assert context.op.tags == {"foo": "oof", "baz": "quux", "bip": "bop"}
        called["yup"] = True

    job_def = GraphDefinition(
        name="metadata_pipeline",
        node_defs=[metadata_op],
        dependencies={
            NodeInvocation(
                "metadata_op",
                alias="aliased_metadata_op",
                tags={"foo": "oof", "bip": "bop"},
            ): {}
        },
    ).to_job()

    result = job_def.execute_in_process()

    assert result.success
    assert called["yup"]


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


def test_metadata_value_column_lineage() -> None:
    expected_column_lineage = TableColumnLineage(
        {"foo": [TableColumnDep(asset_key=AssetKey("bar"), column_name="baz")]}
    )
    column_lineage_metadata_value = MetadataValue.column_lineage(expected_column_lineage)

    assert column_lineage_metadata_value.value == expected_column_lineage


def test_int_metadata_value():
    assert IntMetadataValue(5).value == 5
    assert IntMetadataValue(value=5).value == 5


def test_url_metadata_value():
    url = "http://dagster.io"
    assert UrlMetadataValue(url).value == url
    assert UrlMetadataValue(url).url == url
    assert UrlMetadataValue(url=url).value == url


def test_table_metadata_value():
    records = [TableRecord(dict(foo=1, bar=2))]
    schema = TableSchema(
        columns=[TableColumn(name="foo", type="int"), TableColumn(name="bar", type="int")]
    )
    metadata_val = TableMetadataValue(records, schema=schema)

    assert metadata_val.records == records
    assert metadata_val.schema == schema


def test_table_schema_metadata_value():
    schema = TableSchema(
        columns=[
            TableColumn(name="foo", type="int", tags={"introduced": "v3"}),
            TableColumn(name="bar", type="int"),
        ]
    )
    assert TableSchemaMetadataValue(schema).schema == schema


def test_json_metadata_value():
    assert JsonMetadataValue({"a": "b"}).data == {"a": "b"}
    assert JsonMetadataValue({"a": "b"}).value == {"a": "b"}


def test_code_location_reconstruction_metadata_value():
    assert CodeLocationReconstructionMetadataValue("foo").data == "foo"
    assert CodeLocationReconstructionMetadataValue("foo").value == "foo"

    with pytest.raises(CheckError, match="not a str"):
        CodeLocationReconstructionMetadataValue({"foo": "bar"})


def test_serdes_json_metadata():
    old_bad_event_str = '{"__class__": "JsonMetadataEntryData", "data": {"float": {"__class__": "FloatMetadataEntryData", "value": 1.0}}}'
    val = deserialize_value(old_bad_event_str, JsonMetadataValue)
    assert val
    assert isinstance(val.data["float"], dict)  # and not FloatMetadataValue
    s = serialize_value(val)
    val_2 = deserialize_value(s, JsonMetadataValue)
    assert val_2 == val
