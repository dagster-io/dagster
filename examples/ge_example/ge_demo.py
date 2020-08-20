from dagster_ge.factory import ge_data_context, ge_validation_solid_factory
from pandas import read_csv

from dagster import InputDefinition, ModeDefinition, PresetDefinition, pipeline, solid
from dagster.utils import file_relative_path


@solid
def read_in_datafile(_, csv_path):
    return read_csv(csv_path)


@solid(input_defs=[InputDefinition(name='df')])
def process_payroll(_, df):
    return len(df)


@solid(input_defs=[InputDefinition(name='numrows'), InputDefinition(name='expectation')])
def postprocess_payroll(_, numrows, expectation):
    if expectation["success"]:
        return numrows
    else:
        raise ValueError


payroll_expectations = ge_validation_solid_factory(
    datasource_name="getest", suite_name="basic.warning"
)


@pipeline(
    mode_defs=[ModeDefinition('basic', resource_defs={'ge_data_context': ge_data_context})],
    preset_defs=[
        PresetDefinition(
            'sample_preset_success',
            mode='basic',
            run_config={
                'resources': {
                    'ge_data_context': {
                        'config': {
                            'ge_root_dir': file_relative_path(__file__, "./great_expectations")
                        }
                    }
                },
                'solids': {
                    'read_in_datafile': {
                        'inputs': {
                            'csv_path': {'value': file_relative_path(__file__, './succeed.csv')}
                        }
                    }
                },
            },
        ),
        PresetDefinition(
            'sample_preset_fail',
            mode='basic',
            run_config={
                'resources': {
                    'ge_data_context': {
                        'config': {
                            'ge_root_dir': file_relative_path(__file__, "./great_expectations")
                        }
                    }
                },
                'solids': {
                    'read_in_datafile': {
                        'inputs': {
                            'csv_path': {'value': file_relative_path(__file__, './fail.csv')}
                        }
                    }
                },
            },
        ),
    ],
)
def payroll_data_pipeline():
    output_df = read_in_datafile()

    return postprocess_payroll(process_payroll(output_df), payroll_expectations(output_df))
