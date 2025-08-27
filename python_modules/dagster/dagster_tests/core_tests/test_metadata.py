import dagster as dg
import pytest
from dagster import MetadataValue, TableSchema
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
    ObjectMetadataValue,
    TimestampMetadataValue,
)
from dagster_shared.check import CheckError
from dagster_shared.record import copy
from dagster_shared.serdes.utils import create_snapshot_id


def test_op_instance_tags():
    called = {}

    @dg.op(tags={"foo": "bar", "baz": "quux"})
    def metadata_op(context):
        assert context.op.tags == {"foo": "oof", "baz": "quux", "bip": "bop"}
        called["yup"] = True

    job_def = dg.GraphDefinition(
        name="metadata_pipeline",
        node_defs=[metadata_op],
        dependencies={
            dg.NodeInvocation(
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
    assert TableSchema.from_name_type_dict(
        {"foo": "customtype", "bar": "string"}
    ) == dg.TableSchema(
        columns=[
            dg.TableColumn(name="foo", type="customtype"),
            dg.TableColumn(name="bar", type="string"),
        ],
    )


def test_table_serialization():
    table_metadata = MetadataValue.table(
        records=[
            dg.TableRecord(dict(foo=1, bar=2)),
        ],
    )
    serialized = dg.serialize_value(table_metadata)
    assert dg.deserialize_value(serialized, dg.TableMetadataValue) == table_metadata


def test_metadata_value_column_lineage() -> None:
    expected_column_lineage = dg.TableColumnLineage(
        {"foo": [dg.TableColumnDep(asset_key=dg.AssetKey("bar"), column_name="baz")]}
    )
    column_lineage_metadata_value = MetadataValue.column_lineage(expected_column_lineage)

    assert column_lineage_metadata_value.value == expected_column_lineage


def test_int_metadata_value():
    assert dg.IntMetadataValue(5).value == 5
    assert dg.IntMetadataValue(value=5).value == 5


def test_url_metadata_value():
    url = "http://dagster.io"
    assert dg.UrlMetadataValue(url).value == url
    assert dg.UrlMetadataValue(url).url == url
    assert dg.UrlMetadataValue(url=url).value == url


def test_table_metadata_value():
    records = [dg.TableRecord(dict(foo=1, bar=2))]
    schema = dg.TableSchema(
        columns=[dg.TableColumn(name="foo", type="int"), dg.TableColumn(name="bar", type="int")]
    )
    metadata_val = dg.TableMetadataValue(records, schema=schema)

    assert metadata_val.records == records
    assert metadata_val.schema == schema


def test_table_schema_metadata_value():
    schema = dg.TableSchema(
        columns=[
            dg.TableColumn(name="foo", type="int", tags={"introduced": "v3"}),
            dg.TableColumn(name="bar", type="int"),
        ]
    )
    assert dg.TableSchemaMetadataValue(schema).schema == schema


def test_json_metadata_value():
    assert dg.JsonMetadataValue({"a": "b"}).data == {"a": "b"}
    assert dg.JsonMetadataValue({"a": "b"}).value == {"a": "b"}


def test_code_location_reconstruction_metadata_value():
    assert CodeLocationReconstructionMetadataValue("foo").data == "foo"
    assert CodeLocationReconstructionMetadataValue("foo").value == "foo"

    with pytest.raises(CheckError, match="not a str"):
        CodeLocationReconstructionMetadataValue({"foo": "bar"})  # pyright: ignore[reportArgumentType]


def test_serdes_json_metadata():
    old_bad_event_str = '{"__class__": "JsonMetadataEntryData", "data": {"float": {"__class__": "FloatMetadataEntryData", "value": 1.0}}}'
    val = dg.deserialize_value(old_bad_event_str, dg.JsonMetadataValue)
    assert val
    assert isinstance(
        val.data["float"],  # type: ignore
        dict,
    )
    s = dg.serialize_value(val)
    val_2 = dg.deserialize_value(s, dg.JsonMetadataValue)
    assert val_2 == val


def test_instance_metadata_value():
    class Foo:
        pass

    assert ObjectMetadataValue("foo").class_name == "foo"
    assert ObjectMetadataValue("foo").instance is None

    v = ObjectMetadataValue(Foo())
    assert v.class_name == "Foo"
    assert v.instance is not None

    v2 = copy(v)
    assert v2.class_name == "Foo"
    assert v2.instance is not None

    v3 = dg.deserialize_value(dg.serialize_value(v), ObjectMetadataValue)
    assert v3.class_name == "Foo"
    assert v3.instance is None  # instance lost in serialization

    assert create_snapshot_id(v2) == create_snapshot_id(v3)


def test_serialized_time_entry():
    assert dg.deserialize_value(
        '{"__class__": "TimestampMetadataValue", "value": 1752171695.0141509}',
        TimestampMetadataValue,
    )
