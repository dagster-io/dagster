import csv
import os

from dagster_examples.intro_tutorial.modes import SqlAlchemyPostgresWarehouse as sapw1
from dagster_examples.intro_tutorial.modes import modes_pipeline
from dagster_examples.intro_tutorial.presets import SqlAlchemyPostgresWarehouse as sapw2
from dagster_examples.intro_tutorial.presets import presets_pipeline

from dagster import execute_pipeline_with_mode, execute_pipeline_with_preset
from dagster.utils import pushd, script_relative_path

BUILDKITE = bool(os.getenv('BUILDKITE'))


def test_warehouse(postgres):
    with open(script_relative_path('../../dagster_examples/intro_tutorial/cereal.csv'), 'r') as fd:
        cereals = [row for row in csv.DictReader(fd)]

    for SqlAlchemyPostgresWarehouse in [sapw1, sapw2]:
        warehouse = SqlAlchemyPostgresWarehouse(postgres)
        warehouse.update_normalized_cereals(cereals)


def test_warehouse_resource(postgres):
    environment_dict = {
        'solids': {'read_csv': {'inputs': {'csv_path': {'value': 'cereal.csv'}}}},
        'resources': {'warehouse': {'config': {'conn_str': postgres}}},
    }
    with pushd(script_relative_path('../../dagster_examples/intro_tutorial/')):
        result = execute_pipeline_with_mode(
            pipeline=modes_pipeline, mode='dev', environment_dict=environment_dict,
        )
    assert result.success

    if not BUILDKITE:
        with pushd(script_relative_path('../../dagster_examples/intro_tutorial/')):
            result = execute_pipeline_with_preset(presets_pipeline, preset_name='dev')
        assert result.success
