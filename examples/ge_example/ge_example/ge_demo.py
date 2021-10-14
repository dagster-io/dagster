from dagster import ModeDefinition, PresetDefinition, pipeline, solid
from dagster.utils import file_relative_path
from dagster_ge.factory import ge_data_context, ge_validation_solid_factory
from pandas import read_csv


@solid
def read_in_datafile(csv_path):
    return read_csv(csv_path)


@solid
def process_payroll(df):
    return len(df)


# start_ge_demo_marker_solid


@solid
def postprocess_payroll(numrows, expectation):
    if expectation["success"]:
        return numrows
    else:
        raise ValueError


# end_ge_demo_marker_solid


# start_ge_demo_marker_factory
payroll_expectations = ge_validation_solid_factory(
    name="ge_validation_solid", datasource_name="getest", suite_name="basic.warning"
)
# end_ge_demo_marker_factory


# start_ge_demo_marker_preset

preset_defs = [
    PresetDefinition(
        "sample_preset_success",
        mode="basic",
        run_config={
            "resources": {
                "ge_data_context": {
                    "config": {"ge_root_dir": file_relative_path(__file__, "./great_expectations")}
                }
            },
            "solids": {
                "read_in_datafile": {
                    "inputs": {
                        "csv_path": {"value": file_relative_path(__file__, "./data/succeed.csv")}
                    }
                }
            },
        },
    ),
    PresetDefinition(
        "sample_preset_fail",
        mode="basic",
        run_config={
            "resources": {
                "ge_data_context": {
                    "config": {"ge_root_dir": file_relative_path(__file__, "./great_expectations")}
                }
            },
            "solids": {
                "read_in_datafile": {
                    "inputs": {
                        "csv_path": {"value": file_relative_path(__file__, "./data/fail.csv")}
                    }
                }
            },
        },
    ),
]
# end_ge_demo_marker_preset

# start_ge_demo_marker_pipeline


@pipeline(
    mode_defs=[ModeDefinition("basic", resource_defs={"ge_data_context": ge_data_context})],
    preset_defs=preset_defs,
)
def payroll_data_pipeline():
    output_df = read_in_datafile()

    return postprocess_payroll(process_payroll(output_df), payroll_expectations(output_df))


# end_ge_demo_marker_pipeline
