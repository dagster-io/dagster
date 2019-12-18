from dagster_pandas.constraints import ColumnTypeConstraint
from dagster_pandas.data_frame import create_dagster_pandas_dataframe_type
from dagster_pandas.validation import PandasColumn
from pandas import DataFrame

from dagster import (
    EventMetadataEntry,
    Output,
    OutputDefinition,
    TypeCheck,
    execute_pipeline,
    pipeline,
    solid,
)


def test_create_pandas_dataframe_dagster_type():
    TestDataFrame = create_dagster_pandas_dataframe_type(
        name='TestDataFrame',
        type_check=lambda value: True,
        columns=[PandasColumn(name='foo', constraints=[ColumnTypeConstraint('int64')])],
    )
    assert isinstance(TestDataFrame, type)


def test_mock_pipeline_with_pandas_dataframe_dagster_type():
    def compute_summary_stats(dataframe):
        return [
            EventMetadataEntry.text(str(max(dataframe['pid'])), 'max_pid', 'maximum pid'),
        ]

    def custom_type_check(_):
        return TypeCheck(success=True, metadata_entries=[EventMetadataEntry.text('foo', 'mock')])

    MockDF = create_dagster_pandas_dataframe_type(
        name='MockDF',
        columns=[
            PandasColumn.integer_column('pid', nullable=False),
            PandasColumn.string_column('names'),
        ],
        type_check=custom_type_check,
        summary_statistics=compute_summary_stats,
    )

    @solid(output_defs=[OutputDefinition(name='mock_dataframe', dagster_type=MockDF)])
    def create_dataframe(_):
        yield Output(
            DataFrame({'pid': [1, 2, 3], 'names': ['foo', 'bar', 'baz']}),
            output_name='mock_dataframe',
        )

    @pipeline
    def mock_pipeline():
        return create_dataframe()

    result = execute_pipeline(mock_pipeline)
    assert result.success
    for event in result.event_list:
        if event.event_type_value == 'STEP_OUTPUT':
            mock_df_output_event_metadata = (
                event.event_specific_data.type_check_data.metadata_entries
            )
            assert len(mock_df_output_event_metadata) == 2
            assert any([entry.label == 'mock' for entry in mock_df_output_event_metadata])
            assert any([entry.label == 'max_pid' for entry in mock_df_output_event_metadata])
