from datetime import datetime
from pathlib import Path

import dagster as dg
import pytest
import pytz
from dagster import DagsterEventType, MetadataValue
from dagster._check import CheckError
from dagster._core.definitions.metadata import DagsterInvalidMetadata, normalize_metadata
from dagster._core.execution.execution_result import ExecutionResult
from dagster._core.snap.node import build_node_defs_snapshot


def step_events_of_type(result: ExecutionResult, node_name: str, event_type: DagsterEventType):
    return [
        compute_step_event
        for compute_step_event in result.events_for_node(node_name)
        if compute_step_event.event_type == event_type
    ]


def test_metadata_asset_materialization():
    @dg.op(out={})
    def the_op(_context):
        yield dg.AssetMaterialization(
            asset_key="foo",
            metadata={
                "text": "FOO",
                "int": 22,
                "url": MetadataValue.url("http://fake.com"),
                "float": 0.1,
                "path": MetadataValue.path(Path("/a/b.csv")),
                "python": MetadataValue.python_artifact(dg.MetadataValue),
                "timestamp": MetadataValue.timestamp(2000.5),
                "column_lineage": MetadataValue.column_lineage(
                    dg.TableColumnLineage(
                        {
                            "foo": [
                                dg.TableColumnDep(asset_key=dg.AssetKey("bar"), column_name="baz"),
                            ]
                        }
                    )
                ),
            },
        )

    @dg.job
    def the_job():
        the_op()

    result = the_job.execute_in_process()

    assert result
    assert result.success

    materialization_events = step_events_of_type(
        result, "the_op", DagsterEventType.ASSET_MATERIALIZATION
    )
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert len(materialization.metadata) == 8
    entry_map = {k: v.__class__ for k, v in materialization.metadata.items()}
    assert entry_map["text"] == dg.TextMetadataValue
    assert entry_map["int"] == dg.IntMetadataValue
    assert entry_map["url"] == dg.UrlMetadataValue
    assert entry_map["float"] == dg.FloatMetadataValue
    assert entry_map["path"] == dg.PathMetadataValue
    assert entry_map["python"] == dg.PythonArtifactMetadataValue
    assert entry_map["timestamp"] == dg.TimestampMetadataValue
    assert entry_map["column_lineage"] == dg.TableColumnLineageMetadataValue


def test_metadata_asset_observation():
    @dg.op(out={})
    def the_op(_context):
        yield dg.AssetObservation(
            asset_key="foo",
            metadata={
                "text": "FOO",
                "int": 22,
                "url": MetadataValue.url("http://fake.com"),
                "float": 0.1,
                "python": MetadataValue.python_artifact(dg.MetadataValue),
            },
        )

    @dg.job
    def the_job():
        the_op()

    result = the_job.execute_in_process()

    assert result
    assert result.success

    observation_events = step_events_of_type(result, "the_op", DagsterEventType.ASSET_OBSERVATION)
    assert len(observation_events) == 1
    observation = observation_events[0].event_specific_data.asset_observation  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert len(observation.metadata) == 5
    entry_map = {k: v.__class__ for k, v in observation.metadata.items()}
    assert entry_map["text"] == dg.TextMetadataValue
    assert entry_map["int"] == dg.IntMetadataValue
    assert entry_map["url"] == dg.UrlMetadataValue
    assert entry_map["float"] == dg.FloatMetadataValue
    assert entry_map["python"] == dg.PythonArtifactMetadataValue


def test_metadata_value_timestamp():
    dt_with_timezone = pytz.timezone("America/New_York").localize(datetime(2024, 3, 6, 12, 0, 0))
    metadata_value = MetadataValue.timestamp(dt_with_timezone)
    assert metadata_value.value == dt_with_timezone.timestamp()

    dt_without_timezone = datetime(2024, 3, 6, 12, 0, 0)
    with pytest.raises(
        CheckError, match="Datetime values provided to MetadataValue.timestamp must have timezones"
    ):
        MetadataValue.timestamp(dt_without_timezone)


def test_unknown_metadata_value():
    @dg.op(out={})
    def the_op(context):
        yield dg.AssetMaterialization(
            asset_key="foo",
            metadata={"bad": context.instance},
        )

    @dg.job
    def the_job():
        the_op()

    with pytest.raises(DagsterInvalidMetadata) as exc_info:
        the_job.execute_in_process()

    assert (
        str(exc_info.value) == 'Could not resolve the metadata value for "bad" to a known type. '
        "Its type was <class 'dagster._core.instance.instance.DagsterInstance'>. "
        "Consider wrapping the value with the appropriate MetadataValue type."
    )


def test_parse_null_metadata():
    metadata = {"foo": None}
    normalized = normalize_metadata(metadata)
    assert normalized["foo"] == dg.NullMetadataValue()


def test_parse_list_metadata():
    metadata = {"foo": ["bar"]}
    normalized = normalize_metadata(metadata)
    assert normalized["foo"] == dg.JsonMetadataValue(["bar"])


def test_parse_invalid_metadata():
    metadata = {"foo": object()}

    with pytest.raises(DagsterInvalidMetadata) as _exc_info:
        normalize_metadata(metadata)  # pyright: ignore[reportArgumentType]

    normalized = normalize_metadata(metadata, allow_invalid=True)  # pyright: ignore[reportArgumentType]
    assert normalized["foo"] == dg.TextMetadataValue("[object] (unserializable)")


def test_parse_path_metadata():
    metadata = {"path": Path("/a/b.csv")}
    normalized = normalize_metadata(metadata)
    assert normalized["path"] == dg.PathMetadataValue("/a/b.csv")


def test_bad_json_metadata_value():
    @dg.op(out={})
    def the_op(context):
        yield dg.AssetMaterialization(
            asset_key="foo",
            metadata={"bad": {"nested": context.instance}},
        )

    @dg.job
    def the_job():
        the_op()

    with pytest.raises(DagsterInvalidMetadata) as exc_info:
        the_job.execute_in_process()

    assert (
        str(exc_info.value) == 'Could not resolve the metadata value for "bad" to a known type. '
        "Value is not JSON serializable."
    )


def test_table_metadata_value_schema_inference():
    table = MetadataValue.table(
        records=[
            dg.TableRecord(data=dict(name="foo", status=False)),
            dg.TableRecord(data=dict(name="bar", status=True)),
        ],
    )

    schema = table.schema
    assert isinstance(schema, dg.TableSchema)
    assert schema.columns == [
        dg.TableColumn(name="name", type="string"),
        dg.TableColumn(name="status", type="bool"),
    ]


bad_values = {
    "table_schema": {"columns": False, "constraints": False},
    "table_column": {
        "name": False,
        "type": False,
        "description": False,
        "constraints": False,
    },
    "table_constraints": {"other": False},
    "table_column_constraints": {
        "nullable": "foo",
        "unique": "foo",
        "other": False,
    },
}


def test_table_column_keys():
    with pytest.raises(TypeError):
        dg.TableColumn(bad_key="foo", description="bar", type="string")  # pyright: ignore[reportCallIssue]


@pytest.mark.parametrize("key,value", list(bad_values["table_column"].items()))
def test_table_column_values(key, value):
    kwargs = {
        "name": "foo",
        "type": "string",
        "description": "bar",
        "constraints": dg.TableColumnConstraints(other=["foo"]),
    }
    kwargs[key] = value
    with pytest.raises(CheckError):
        dg.TableColumn(**kwargs)


def test_table_constraints_keys():
    with pytest.raises(TypeError):
        dg.TableColumn(bad_key="foo")  # pyright: ignore[reportCallIssue]


@pytest.mark.parametrize("key,value", list(bad_values["table_constraints"].items()))
def test_table_constraints(key, value):
    kwargs = {"other": ["foo"]}
    kwargs[key] = value
    with pytest.raises(CheckError):
        dg.TableConstraints(**kwargs)


def test_table_column_constraints_keys():
    with pytest.raises(TypeError):
        dg.TableColumnConstraints(bad_key="foo")  # pyright: ignore[reportCallIssue]


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
        dg.TableColumnConstraints(**kwargs)


def test_table_schema_keys():
    with pytest.raises(TypeError):
        dg.TableSchema(bad_key="foo")  # pyright: ignore[reportCallIssue]


@pytest.mark.parametrize("key,value", list(bad_values["table_schema"].items()))
def test_table_schema_values(key, value):
    kwargs = {
        "constraints": dg.TableConstraints(other=["foo"]),
        "columns": [
            dg.TableColumn(
                name="foo",
                type="string",
                description="bar",
                constraints=dg.TableColumnConstraints(other=["foo"]),
            )
        ],
    }
    kwargs[key] = value
    with pytest.raises(CheckError):
        dg.TableSchema(**kwargs)


def test_complex_table_schema():
    assert isinstance(
        dg.TableSchema(
            columns=[
                dg.TableColumn(
                    name="foo",
                    type="customtype",
                    constraints=dg.TableColumnConstraints(
                        nullable=True,
                        unique=True,
                    ),
                ),
                dg.TableColumn(
                    name="bar",
                    type="string",
                    description="bar",
                    constraints=dg.TableColumnConstraints(
                        nullable=False,
                        other=["foo"],
                    ),
                ),
            ],
            constraints=dg.TableConstraints(other=["foo"]),
        ),
        dg.TableSchema,
    )


def test_bool_metadata_value():
    @dg.op(out={})
    def the_op():
        yield dg.AssetMaterialization(
            asset_key="foo",
            metadata={"first_bool": True, "second_bool": dg.BoolMetadataValue(False)},
        )

    @dg.job
    def the_job():
        the_op()

    result = the_job.execute_in_process()

    assert result
    assert result.success

    materialization_events = step_events_of_type(
        result, "the_op", DagsterEventType.ASSET_MATERIALIZATION
    )
    assert len(materialization_events) == 1
    materialization = materialization_events[0].event_specific_data.materialization  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    entry_map = {k: v.__class__ for k, v in materialization.metadata.items()}
    assert entry_map["first_bool"] == dg.BoolMetadataValue
    assert entry_map["second_bool"] == dg.BoolMetadataValue


def test_snapshot_arbitrary_metadata():
    # Asset decorator accepts arbitrary metadata. Need to ensure this doesn't throw an error when a
    # snap is created.
    @dg.asset(metadata={"my_key": [object()]})
    def foo_asset():
        pass

    assert build_node_defs_snapshot(
        dg.Definitions(assets=[foo_asset]).resolve_implicit_global_asset_job_def()
    )
