import pandas as pd
from dagster import DagsterEventType, In, file_relative_path, graph, op
from dagster_pandas import DataFrame


def test_basic_pd_df_metadata():
    @op
    def return_num_csv():
        return pd.read_csv(file_relative_path(__file__, "num.csv"))

    @op(ins={"df": In(DataFrame)})
    def noop(df):
        return df

    @graph
    def basic_graph():
        noop(return_num_csv())

    result = basic_graph.execute_in_process()

    assert result.success

    op_events = result.events_for_node("noop")

    input_events = [event for event in op_events if event.event_type == DagsterEventType.STEP_INPUT]
    assert len(input_events) == 1
    input_event = input_events[0]

    assert input_event.step_input_data.input_name == "df"

    metadata_entries = input_event.step_input_data.type_check_data.metadata_entries

    assert metadata_entries[0].label == "row_count"
    assert metadata_entries[0].entry_data.text == "2"

    assert metadata_entries[1].label == "metadata"
    assert metadata_entries[1].entry_data.data["columns"] == ["num1", "num2"]
