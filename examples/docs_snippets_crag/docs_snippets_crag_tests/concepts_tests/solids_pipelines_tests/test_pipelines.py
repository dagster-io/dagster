from dagster import execute_pipeline
from docs_snippets_crag.concepts.solids_pipelines.branching_pipeline import branching_pipeline
from docs_snippets_crag.concepts.solids_pipelines.dynamic_pipeline.dynamic_pipeline import (
    process_directory,
)
from docs_snippets_crag.concepts.solids_pipelines.fan_in_pipeline import fan_in_pipeline
from docs_snippets_crag.concepts.solids_pipelines.linear_pipeline import linear_pipeline
from docs_snippets_crag.concepts.solids_pipelines.multiple_io_pipeline import (
    inputs_and_outputs_pipeline,
)
from docs_snippets_crag.concepts.solids_pipelines.order_based_dependency_pipeline import (
    nothing_dependency_pipeline,
)
from docs_snippets_crag.concepts.solids_pipelines.pipelines import (
    alias_pipeline,
    one_plus_one_pipeline,
    one_plus_one_pipeline_def,
    tag_pipeline,
)


def test_one_plus_one_pipeline():
    result = execute_pipeline(one_plus_one_pipeline)
    assert result.output_for_solid("add_one", output_name="result") == 2


def test_one_plus_one_pipeline_def():
    result = execute_pipeline(one_plus_one_pipeline_def)
    assert result.output_for_solid("add_one", output_name="result") == 2


def test_linear_pipeline():
    result = execute_pipeline(linear_pipeline)
    assert result.output_for_solid("add_one_3", output_name="result") == 4


def test_other_pipelines():
    other_pipelines = [
        branching_pipeline,
        inputs_and_outputs_pipeline,
        nothing_dependency_pipeline,
        alias_pipeline,
        tag_pipeline,
    ]
    for pipeline in other_pipelines:
        result = execute_pipeline(pipeline)
        assert result.success


def test_fan_in_pipeline():
    result = execute_pipeline(fan_in_pipeline)
    assert result.success
    assert result.result_for_solid("sum_fan_in").output_value() == 10


def test_dynamic_pipeline():
    result = execute_pipeline(process_directory)
    assert result.success

    assert result.result_for_solid("process_file").output_value() == {
        "empty_stuff_bin": 0,
        "program_py": 34,
        "words_txt": 40,
    }
    assert result.result_for_solid("summarize_directory").output_value() == 74
