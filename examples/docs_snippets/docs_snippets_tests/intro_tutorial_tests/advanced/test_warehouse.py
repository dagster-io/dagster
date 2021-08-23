import csv
import os

from dagster import execute_pipeline
from dagster.utils import script_relative_path
from docs_snippets.intro_tutorial.advanced.pipelines.modes import (
    SqlAlchemyPostgresWarehouse as sapw1,
)
from docs_snippets.intro_tutorial.advanced.pipelines.modes import modes_pipeline
from docs_snippets.intro_tutorial.advanced.pipelines.presets import (
    SqlAlchemyPostgresWarehouse as sapw2,
)
from docs_snippets.intro_tutorial.advanced.pipelines.presets import presets_pipeline
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests

BUILDKITE = bool(os.getenv("BUILDKITE"))


def test_warehouse(postgres):
    with open(script_relative_path("../../../docs_snippets/intro_tutorial/cereal.csv"), "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]

    for SqlAlchemyPostgresWarehouse in [sapw1, sapw2]:
        warehouse = SqlAlchemyPostgresWarehouse(postgres)
        warehouse.update_normalized_cereals(cereals)


def test_warehouse_resource(postgres):
    run_config = {"resources": {"warehouse": {"config": {"conn_str": postgres}}}}

    @patch_cereal_requests
    def execute_with_mode():
        result = execute_pipeline(
            pipeline=modes_pipeline,
            mode="dev",
            run_config=run_config,
        )
        assert result.success

    execute_with_mode()

    if not BUILDKITE:

        @patch_cereal_requests
        def execute_with_presets():
            result = execute_pipeline(presets_pipeline, preset="unittest")
            assert result.success

        execute_with_presets()
