import pandas as pd
from dagster_pandas import DataFrame

from dagster import InputDefinition, execute_pipeline, file_relative_path, lambda_solid, pipeline


def test_basic_pd_df_input_metadata():
    @lambda_solid
    def return_num_csv():
        return pd.read_csv(file_relative_path(__file__, "num.csv"))

    @lambda_solid(input_defs=[InputDefinition("df", DataFrame)])
    def noop(df):
        return df

    @pipeline
    def pipe():
        noop(return_num_csv())

    result = execute_pipeline(pipe)

    assert result.success

    solid_result = result.result_for_solid("noop")

    input_event_dict = solid_result.compute_input_event_dict

    assert len(input_event_dict) == 1

    df_input_event = input_event_dict["df"]

    metadata_entries = df_input_event.event_specific_data.type_check_data.metadata_entries

    assert metadata_entries[0].label == "row_count"
    assert metadata_entries[0].entry_data.text == "2"

    assert metadata_entries[1].label == "metadata"
    assert metadata_entries[1].entry_data.data["columns"] == ["num1", "num2"]
