from dagster import Config, job, op
from dagster._utils import file_relative_path
from dagster_ge.factory import ge_validation_op_factory
from pandas import read_csv


class GEOpConfig(Config):
    csv_path: str = file_relative_path(__file__, "./data/succeed.csv")


@op
def read_in_datafile(config: GEOpConfig):
    return read_csv(config.csv_path)


@op
def process_payroll(df):
    return len(df)


# start_ge_demo_marker_op
@op
def postprocess_payroll(numrows, expectation):
    if expectation["success"]:
        return numrows
    else:
        raise ValueError


# end_ge_demo_marker_op


# start_ge_demo_marker_factory
payroll_expectations = ge_validation_op_factory(
    name="ge_validation_op",
    datasource_name="getest",
    data_connector_name="my_runtime_data_connector",
    data_asset_name="test_asset",
    suite_name="basic.warning",
    batch_identifiers={"foo": "bar"},
)
# end_ge_demo_marker_factory


# start_ge_demo_marker_job
@job
def payroll_data():
    output_df = read_in_datafile()

    postprocess_payroll(process_payroll(output_df), payroll_expectations(output_df))


# end_ge_demo_marker_job
