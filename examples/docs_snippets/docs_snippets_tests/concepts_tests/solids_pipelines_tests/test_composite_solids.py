import yaml

from dagster import job
from dagster.utils import file_relative_path
from docs_snippets.concepts.solids_pipelines.composite_solids import (
    all_together_nested,
    subgraph_config_job,
    subgraph_multiple_outputs_job,
)
from docs_snippets.concepts.solids_pipelines.graph_provides_config import (
    celsius_to_fahrenheit,
)
from docs_snippets.concepts.solids_pipelines.graph_provides_config_mapping import (
    to_fahrenheit,
)
from docs_snippets.concepts.solids_pipelines.unnested_ops import (
    all_together_unnested,
    return_fifty,
)


def test_unnested():
    assert all_together_unnested.execute_in_process().success


def test_nested():
    assert all_together_nested.execute_in_process().success


def test_composite_config():
    with open(
        file_relative_path(
            __file__,
            "../../../docs_snippets/concepts/solids_pipelines/composite_config.yaml",
        ),
        "r", encoding="utf8",
    ) as fd:
        run_config = yaml.safe_load(fd.read())

    assert subgraph_config_job.execute_in_process(run_config=run_config).success


def test_graph_provides_config():
    @job
    def my_job():
        celsius_to_fahrenheit(return_fifty())

    my_job.execute_in_process()


def test_config_mapping():
    @job
    def my_job():
        to_fahrenheit(return_fifty())

    with open(
        file_relative_path(
            __file__,
            "../../../docs_snippets/concepts/solids_pipelines/composite_config_mapping.yaml",
        ),
        "r", encoding="utf8",
    ) as fd:
        run_config = yaml.safe_load(fd.read())

    assert my_job.execute_in_process(run_config=run_config).success


def test_composite_multi_outputs():
    assert subgraph_multiple_outputs_job.execute_in_process().success
