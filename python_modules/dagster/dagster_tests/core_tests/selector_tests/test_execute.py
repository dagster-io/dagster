import re

import pytest

from dagster import execute_pipeline, execute_pipeline_iterator
from dagster.core.definitions.executable import InMemoryExecutablePipeline
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.core.test_utils import step_output_event_filter

from .test_subset_selector import foo_pipeline


def test_subset_for_execution():
    pipeline = InMemoryExecutablePipeline(foo_pipeline)
    sub_pipeline = pipeline.subset_for_execution(["*add_nums"])
    assert sub_pipeline.solid_selection == ["*add_nums"]
    assert sub_pipeline.solids_to_execute == {"add_nums", "return_one", "return_two"}

    result = execute_pipeline(sub_pipeline)
    assert result.success


def test_execute_pipeline_with_solid_selection_single_clause():
    pipeline_result_full = execute_pipeline(foo_pipeline)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    pipeline_result_up = execute_pipeline(foo_pipeline, solid_selection=["*add_nums"])
    assert pipeline_result_up.success
    assert pipeline_result_up.result_for_solid("add_nums").output_value() == 3
    assert len(pipeline_result_up.solid_result_list) == 3

    pipeline_result_down = execute_pipeline(
        foo_pipeline,
        run_config={
            "solids": {"add_nums": {"inputs": {"num1": {"value": 1}, "num2": {"value": 2}}}}
        },
        solid_selection=["add_nums++"],
    )
    assert pipeline_result_down.success
    assert pipeline_result_down.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_down.solid_result_list) == 3


def test_execute_pipeline_with_solid_selection_multi_clauses():
    result_multi_disjoint = execute_pipeline(
        foo_pipeline, solid_selection=["return_one", "return_two", "add_nums+"]
    )
    assert result_multi_disjoint.success
    assert result_multi_disjoint.result_for_solid("multiply_two").output_value() == 6
    assert len(result_multi_disjoint.solid_result_list) == 4

    result_multi_overlap = execute_pipeline(
        foo_pipeline, solid_selection=["return_one++", "add_nums+", "return_two"]
    )
    assert result_multi_overlap.success
    assert result_multi_overlap.result_for_solid("multiply_two").output_value() == 6
    assert len(result_multi_overlap.solid_result_list) == 4

    result_multi_with_invalid = execute_pipeline(foo_pipeline, solid_selection=["a", "*add_nums"])
    assert result_multi_with_invalid.success
    assert result_multi_with_invalid.result_for_solid("add_nums").output_value() == 3
    assert len(result_multi_with_invalid.solid_result_list) == 3


def test_execute_pipeline_with_solid_selection_invalid():
    invalid_input = ["return_one,return_two"]

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=re.escape(
            "No qualified solids to execute found for solid_selection={input}".format(
                input=invalid_input
            )
        ),
    ):
        execute_pipeline(foo_pipeline, solid_selection=invalid_input)


def test_execute_pipeline_iterator_with_solid_selection_query():

    output_event_iterator = step_output_event_filter(execute_pipeline_iterator(foo_pipeline))
    events = list(output_event_iterator)
    assert len(events) == 5

    iterator_up = step_output_event_filter(
        execute_pipeline_iterator(foo_pipeline, solid_selection=["*add_nums"])
    )
    events_up = list(iterator_up)
    assert len(events_up) == 3

    iterator_down = step_output_event_filter(
        execute_pipeline_iterator(
            foo_pipeline,
            run_config={
                "solids": {"add_nums": {"inputs": {"num1": {"value": 1}, "num2": {"value": 2}}}}
            },
            solid_selection=["add_nums++"],
        )
    )
    events_down = list(iterator_down)
    assert len(events_down) == 3
