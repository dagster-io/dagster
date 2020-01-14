import pytest
from dagster_pandas.constraints import (
    ColumnTypeConstraint,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
)
from dagster_pandas.data_frame import create_dagster_pandas_dataframe_type
from dagster_pandas.validation import PandasColumn
from pandas import DataFrame

from dagster import (
    DagsterInvariantViolationError,
    EventMetadataEntry,
    Output,
    OutputDefinition,
    RuntimeType,
    check_dagster_type,
    execute_pipeline,
    pipeline,
    solid,
)


def test_create_pandas_dataframe_dagster_type():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        columns=[PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
    )
    assert isinstance(TestDataFrame, RuntimeType)


def test_basic_pipeline_with_pandas_dataframe_dagster_type():
    def compute_event_metadata(dataframe):
        return [
            EventMetadataEntry.text(str(max(dataframe['pid'])), 'max_pid', 'maximum pid'),
        ]

    BasicDF = create_dagster_pandas_dataframe_type(
        name='BasicDF',
        columns=[
            PandasColumn.integer_column('pid', exists=True),
            PandasColumn.string_column('names'),
        ],
        event_metadata_fn=compute_event_metadata,
    )

    @solid(output_defs=[OutputDefinition(name='basic_dataframe', dagster_type=BasicDF)])
    def create_dataframe(_):
        yield Output(
            DataFrame({'pid': [1, 2, 3], 'names': ['foo', 'bar', 'baz']}),
            output_name='basic_dataframe',
        )

    @pipeline
    def basic_pipeline():
        return create_dataframe()

    result = execute_pipeline(basic_pipeline)
    assert result.success
    for event in result.event_list:
        if event.event_type_value == 'STEP_OUTPUT':
            mock_df_output_event_metadata = (
                event.event_specific_data.type_check_data.metadata_entries
            )
            assert len(mock_df_output_event_metadata) == 1
            assert any([entry.label == 'max_pid' for entry in mock_df_output_event_metadata])


def test_bad_dataframe_type_returns_bad_stuff():
    with pytest.raises(DagsterInvariantViolationError):
        BadDFBadSummaryStats = create_dagster_pandas_dataframe_type(
            'BadDF', event_metadata_fn=lambda _: 'ksjdkfsd'
        )
        check_dagster_type(BadDFBadSummaryStats, DataFrame({'num': [1]}))

    with pytest.raises(DagsterInvariantViolationError):
        BadDFBadSummaryStatsListItem = create_dagster_pandas_dataframe_type(
            'BadDF', event_metadata_fn=lambda _: ['ksjdkfsd']
        )
        check_dagster_type(BadDFBadSummaryStatsListItem, DataFrame({'num': [1]}))


def test_dataframe_description_generation_just_type_constraint():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        columns=[PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
    )
    assert TestDataFrame.description == "\n### Columns\n**foo**: `int64`\n\n"


def test_dataframe_description_generation_no_type_constraint():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame', columns=[PandasColumn(name='foo')],
    )
    assert TestDataFrame.description == "\n### Columns\n**foo**\n\n"


def test_dataframe_description_generation_multi_constraints():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        columns=[
            PandasColumn(
                name='foo',
                constraints=[
                    ColumnTypeConstraint('int64'),
                    InRangeColumnConstraint(0, 100),
                    NonNullableColumnConstraint(),
                ],
            ),
        ],
    )
    assert (
        TestDataFrame.description
        == "\n### Columns\n**foo**: `int64`\n+ 0 < values < 100\n+ No Null values allowed.\n\n"
    )
