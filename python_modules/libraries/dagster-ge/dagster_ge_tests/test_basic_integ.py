from dagster_ge.factory import ge_data_context, ge_validation_solid_factory
from pandas import read_csv

from dagster import (
    DagsterInstance,
    InputDefinition,
    ModeDefinition,
    Output,
    execute_pipeline,
    pipeline,
    reconstructable,
    solid,
)
from dagster.utils import file_relative_path


@solid
def yielder(_):
    return read_csv("./basic.csv")


@solid(input_defs=[InputDefinition(name='res')])
def reyielder(_context, res):
    yield Output((res['statistics'], res['results']))


@pipeline(mode_defs=[ModeDefinition('basic', resource_defs={'ge_data_context': ge_data_context})],)
def hello_world_pipeline():
    return reyielder(ge_validation_solid_factory("getest", "basic.warning")(yielder()))


def test_yielded_results_config(snapshot):
    run_config = {
        'resources': {
            'ge_data_context': {
                'config': {'ge_root_dir': file_relative_path(__file__, "./great_expectations")}
            }
        }
    }
    result = execute_pipeline(
        reconstructable(hello_world_pipeline),
        run_config=run_config,
        mode='basic',
        instance=DagsterInstance.local_temp(),
    )
    assert result.result_for_solid("reyielder").output_value()[0]["success_percent"] == 100
    expectations = result.result_for_solid("ge_validation_solid").expectation_results_during_compute
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    # purge system specific metadata for testing
    metadata = mainexpect.metadata_entries[0].entry_data.md_str.split("### Info")[0]
    snapshot.assert_match(metadata)
