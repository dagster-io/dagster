import re

import pytest
from dagster import (
    execute_pipeline,
    execute_pipeline_iterator,
    reexecute_pipeline,
    reexecute_pipeline_iterator,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.errors import DagsterExecutionStepNotFoundError, DagsterInvalidSubsetError
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import step_output_event_filter

from .test_subset_selector import foo_pipeline


def test_subset_for_execution():
    pipeline = InMemoryPipeline(foo_pipeline)
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

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=re.escape("No qualified solids to execute found for solid_selection"),
    ):
        execute_pipeline(foo_pipeline, solid_selection=["a", "*add_nums"])


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


def test_reexecute_pipeline_with_step_selection_single_clause():
    instance = DagsterInstance.ephemeral()
    run_config = {"intermediate_storage": {"filesystem": {}}}
    pipeline_result_full = execute_pipeline(foo_pipeline, run_config=run_config, instance=instance)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    reexecution_result_full = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        run_config=run_config,
        instance=instance,
    )

    assert reexecution_result_full.success
    assert len(reexecution_result_full.solid_result_list) == 5
    assert reexecution_result_full.result_for_solid("add_one").output_value() == 7

    reexecution_result_up = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["*add_nums"],
    )

    assert reexecution_result_up.success
    assert reexecution_result_up.result_for_solid("add_nums").output_value() == 3

    reexecution_result_down = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["add_nums++"],
    )
    assert reexecution_result_down.success
    assert reexecution_result_down.result_for_solid("add_one").output_value() == 7


def test_reexecute_pipeline_with_step_selection_multi_clauses():
    instance = DagsterInstance.ephemeral()
    run_config = {"intermediate_storage": {"filesystem": {}}}
    pipeline_result_full = execute_pipeline(foo_pipeline, run_config=run_config, instance=instance)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    result_multi_disjoint = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["return_one", "return_two", "add_nums+"],
    )
    assert result_multi_disjoint.success
    assert result_multi_disjoint.result_for_solid("multiply_two").output_value() == 6

    result_multi_overlap = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        run_config=run_config,
        instance=instance,
        step_selection=["return_one++", "return_two", "add_nums+"],
    )
    assert result_multi_overlap.success
    assert result_multi_overlap.result_for_solid("multiply_two").output_value() == 6

    with pytest.raises(
        DagsterExecutionStepNotFoundError,
        match="Can not build subset plan from unknown step: a",
    ):
        reexecute_pipeline(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            run_config=run_config,
            instance=instance,
            step_selection=["a", "*add_nums"],
        )


def test_reexecute_pipeline_iterator():
    instance = DagsterInstance.ephemeral()
    run_config = {"intermediate_storage": {"filesystem": {}}}
    pipeline_result_full = execute_pipeline(foo_pipeline, run_config=run_config, instance=instance)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    output_event_iterator_full = step_output_event_filter(
        reexecute_pipeline_iterator(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            run_config=run_config,
            instance=instance,
        )
    )
    events_full = list(output_event_iterator_full)
    assert len(events_full) == 5

    output_event_iterator_up = step_output_event_filter(
        reexecute_pipeline_iterator(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            run_config=run_config,
            instance=instance,
            step_selection=["*add_nums"],
        )
    )
    events_up = list(output_event_iterator_up)
    assert len(events_up) == 3
