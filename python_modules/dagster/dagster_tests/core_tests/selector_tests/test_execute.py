import re

import pytest

from dagster import (
    execute_pipeline,
    execute_pipeline_iterator,
    reexecute_pipeline,
    reexecute_pipeline_iterator,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.errors import DagsterExecutionStepNotFoundError, DagsterInvalidSubsetError
from dagster._core.execution.api import create_execution_plan, execute_run
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import instance_for_test, step_output_event_filter

from .test_subset_selector import asset_selection_job, foo_pipeline


def test_subset_for_execution():
    pipeline = InMemoryPipeline(foo_pipeline)
    sub_pipeline = pipeline.subset_for_execution(["*add_nums"], asset_selection=None)
    assert sub_pipeline.solid_selection == ["*add_nums"]
    assert sub_pipeline.solids_to_execute == {"add_nums", "return_one", "return_two"}

    result = execute_pipeline(sub_pipeline)
    assert result.success


def test_asset_subset_for_execution():
    in_mem_pipeline = InMemoryPipeline(asset_selection_job)
    sub_pipeline = in_mem_pipeline.subset_for_execution(
        solid_selection=None, asset_selection={AssetKey("my_asset")}
    )
    assert sub_pipeline.asset_selection == {AssetKey("my_asset")}

    result = execute_pipeline(sub_pipeline)
    assert result.success
    materializations = [event for event in result.step_event_list if event.is_step_materialization]
    assert len(materializations) == 1
    assert materializations[0].asset_key == AssetKey("my_asset")

    with instance_for_test() as instance:
        execution_plan = create_execution_plan(sub_pipeline)
        pipeline_run = instance.create_run_for_pipeline(
            asset_selection_job,
            asset_selection={AssetKey("my_asset")},
            execution_plan=execution_plan,
        )

        result = execute_run(in_mem_pipeline, pipeline_run, instance)
        assert result.success
        materializations = [
            event for event in result.step_event_list if event.is_step_materialization
        ]
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey("my_asset")


def test_reexecute_asset_subset():
    with instance_for_test() as instance:
        result = asset_selection_job.execute_in_process(
            instance=instance, asset_selection=[AssetKey("my_asset")]
        )
        assert result.success
        materializations = [event for event in result.all_events if event.is_step_materialization]
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey("my_asset")

        run = instance.get_run_by_id(result.run_id)
        assert run.asset_selection == {AssetKey("my_asset")}

        reexecution_result = reexecute_pipeline(
            asset_selection_job,
            parent_run_id=result.run_id,
            instance=instance,
        )
        assert reexecution_result.success
        materializations = [
            event for event in reexecution_result.step_event_list if event.is_step_materialization
        ]
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey("my_asset")
        run = instance.get_run_by_id(reexecution_result.run_id)
        assert run.asset_selection == {AssetKey("my_asset")}


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
    pipeline_result_full = execute_pipeline(foo_pipeline, instance=instance)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    reexecution_result_full = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        instance=instance,
    )

    assert reexecution_result_full.success
    assert len(reexecution_result_full.solid_result_list) == 5
    assert reexecution_result_full.result_for_solid("add_one").output_value() == 7

    reexecution_result_up = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        instance=instance,
        step_selection=["*add_nums"],
    )

    assert reexecution_result_up.success
    assert reexecution_result_up.result_for_solid("add_nums").output_value() == 3

    reexecution_result_down = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        instance=instance,
        step_selection=["add_nums++"],
    )
    assert reexecution_result_down.success
    assert reexecution_result_down.result_for_solid("add_one").output_value() == 7


def test_reexecute_pipeline_with_step_selection_multi_clauses():
    instance = DagsterInstance.ephemeral()
    pipeline_result_full = execute_pipeline(foo_pipeline, instance=instance)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    result_multi_disjoint = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        instance=instance,
        step_selection=["return_one", "return_two", "add_nums+"],
    )
    assert result_multi_disjoint.success
    assert result_multi_disjoint.result_for_solid("multiply_two").output_value() == 6

    result_multi_overlap = reexecute_pipeline(
        foo_pipeline,
        parent_run_id=pipeline_result_full.run_id,
        instance=instance,
        step_selection=["return_one++", "return_two", "add_nums+"],
    )
    assert result_multi_overlap.success
    assert result_multi_overlap.result_for_solid("multiply_two").output_value() == 6

    with pytest.raises(
        DagsterExecutionStepNotFoundError,
        match="Step selection refers to unknown step: a",
    ):
        reexecute_pipeline(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            instance=instance,
            step_selection=["a", "*add_nums"],
        )

    with pytest.raises(
        DagsterExecutionStepNotFoundError,
        match="Step selection refers to unknown steps: a, b",
    ):
        reexecute_pipeline(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            instance=instance,
            step_selection=["a+", "*b"],
        )


def test_reexecute_pipeline_iterator():
    instance = DagsterInstance.ephemeral()
    pipeline_result_full = execute_pipeline(foo_pipeline, instance=instance)
    assert pipeline_result_full.success
    assert pipeline_result_full.result_for_solid("add_one").output_value() == 7
    assert len(pipeline_result_full.solid_result_list) == 5

    output_event_iterator_full = step_output_event_filter(
        reexecute_pipeline_iterator(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            instance=instance,
        )
    )
    events_full = list(output_event_iterator_full)
    assert len(events_full) == 5

    output_event_iterator_up = step_output_event_filter(
        reexecute_pipeline_iterator(
            foo_pipeline,
            parent_run_id=pipeline_result_full.run_id,
            instance=instance,
            step_selection=["*add_nums"],
        )
    )
    events_up = list(output_event_iterator_up)
    assert len(events_up) == 3
