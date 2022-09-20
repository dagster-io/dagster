import re

import pytest

from dagster import ReexecutionOptions, execute_job, reconstructable
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterExecutionStepNotFoundError, DagsterInvalidSubsetError
from dagster._core.test_utils import instance_for_test

from .test_subset_selector import foo_job, get_asset_selection_job


def test_subset_for_execution():
    recon_job = reconstructable(foo_job)
    sub_job = recon_job.subset_for_execution(["*add_nums"])

    assert sub_job.solid_selection == ["*add_nums"]
    assert sub_job.solids_to_execute is None

    with instance_for_test() as instance:
        result = execute_job(sub_job, instance)
        assert result.success
        assert set([event.step_key for event in result.all_events if event.is_step_event]) == {
            "add_nums",
            "return_one",
            "return_two",
        }


def test_asset_subset_for_execution():
    recon_job = reconstructable(get_asset_selection_job)
    sub_job = recon_job.subset_for_execution(
        solid_selection=None, asset_selection={AssetKey("my_asset")}
    )
    assert sub_job.asset_selection == {AssetKey("my_asset")}

    with instance_for_test() as instance:
        result = execute_job(sub_job, instance, asset_selection=[AssetKey("my_asset")])
        assert result.success

        materializations = result.filter_events(lambda evt: evt.is_step_materialization)
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey("my_asset")


def test_reexecute_asset_subset():
    with instance_for_test() as instance:
        result = execute_job(
            reconstructable(get_asset_selection_job),
            instance,
            asset_selection=[AssetKey("my_asset")],
        )
        assert result.success
        materializations = [event for event in result.all_events if event.is_step_materialization]
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey("my_asset")

        run = instance.get_run_by_id(result.run_id)
        assert run.asset_selection == {AssetKey("my_asset")}

        reexecution_result = execute_job(
            reconstructable(get_asset_selection_job),
            instance,
            reexecution_options=ReexecutionOptions(parent_run_id=result.run_id),
        )

        assert reexecution_result.success
        materializations = reexecution_result.filter_events(lambda evt: evt.is_step_materialization)
        assert len(materializations) == 1
        assert materializations[0].asset_key == AssetKey("my_asset")
        run = instance.get_run_by_id(reexecution_result.run_id)
        assert run.asset_selection == {AssetKey("my_asset")}


def test_execute_job_with_solid_selection_single_clause():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(foo_job),
            instance,
        ) as pipeline_result_full:
            assert pipeline_result_full.success
            assert pipeline_result_full.output_for_node("add_one") == 7
            assert len(pipeline_result_full.get_step_success_events()) == 5

        with execute_job(
            reconstructable(foo_job), op_selection=["*add_nums"], instance=instance
        ) as pipeline_result_up:
            assert pipeline_result_up.success
            assert pipeline_result_up.output_for_node("add_nums") == 3
            assert len(pipeline_result_up.get_step_success_events()) == 3

        with execute_job(
            reconstructable(foo_job),
            instance,
            run_config={
                "solids": {"add_nums": {"inputs": {"num1": {"value": 1}, "num2": {"value": 2}}}}
            },
            op_selection=["add_nums++"],
        ) as job_result_down:
            assert job_result_down.success
            assert job_result_down.output_for_node("add_one") == 7
            assert len(job_result_down.get_step_success_events()) == 3


def test_execute_job_with_solid_selection_multi_clauses():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(foo_job),
            instance,
            op_selection=["return_one", "return_two", "add_nums+"],
        ) as result_multi_disjoint:
            assert result_multi_disjoint.success
            assert result_multi_disjoint.output_for_node("multiply_two") == 6
            assert len(result_multi_disjoint.get_step_success_events()) == 4

        with execute_job(
            reconstructable(foo_job),
            instance,
            op_selection=["return_one++", "add_nums+", "return_two"],
        ) as result_multi_overlap:
            assert result_multi_overlap.success
            assert result_multi_overlap.output_for_node("multiply_two") == 6
            assert len(result_multi_overlap.get_step_success_events()) == 4

        with pytest.raises(
            DagsterInvalidSubsetError,
            match=re.escape("No qualified ops to execute found for op_selection"),
        ):
            execute_job(reconstructable(foo_job), instance, op_selection=["a", "*add_nums"])


def test_execute_job_with_solid_selection_invalid():
    invalid_input = ["return_one,return_two"]

    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvalidSubsetError,
            match=re.escape(
                "No qualified ops to execute found for op_selection={input}".format(
                    input=invalid_input
                )
            ),
        ):
            execute_job(reconstructable(foo_job), op_selection=invalid_input, instance=instance)


def test_reexecute_job_with_step_selection_single_clause():
    with instance_for_test() as instance:
        with execute_job(reconstructable(foo_job), instance=instance) as pipeline_result_full:
            assert pipeline_result_full.success
            assert pipeline_result_full.output_for_node("add_one") == 7
            assert len(pipeline_result_full.get_step_success_events()) == 5

            with execute_job(
                reconstructable(foo_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(parent_run_id=pipeline_result_full.run_id),
            ) as reexecution_result_full:

                assert reexecution_result_full.success
                assert len(reexecution_result_full.get_step_success_events()) == 5
                assert reexecution_result_full.output_for_node("add_one") == 7

            with execute_job(
                reconstructable(foo_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=pipeline_result_full.run_id,
                    step_selection=["*add_nums"],
                ),
            ) as reexecution_result_up:

                assert reexecution_result_up.success
                assert reexecution_result_up.output_for_node("add_nums") == 3

            with execute_job(
                reconstructable(foo_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=pipeline_result_full.run_id,
                    step_selection=["add_nums++"],
                ),
                raise_on_error=True,
            ) as reexecution_result_down:
                assert reexecution_result_down.success
                assert reexecution_result_down.output_for_node("add_one") == 7


def test_reexecute_job_with_step_selection_multi_clauses():
    with instance_for_test() as instance:
        with execute_job(reconstructable(foo_job), instance=instance) as pipeline_result_full:
            assert pipeline_result_full.success
            assert pipeline_result_full.output_for_node("add_one") == 7
            assert len(pipeline_result_full.get_step_success_events()) == 5

        with execute_job(
            reconstructable(foo_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=pipeline_result_full.run_id,
                step_selection=["return_one", "return_two", "add_nums+"],
            ),
        ) as result_multi_disjoint:
            assert result_multi_disjoint.success
            assert result_multi_disjoint.output_for_node("multiply_two") == 6

        with execute_job(
            reconstructable(foo_job),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=pipeline_result_full.run_id,
                step_selection=["return_one++", "return_two", "add_nums+"],
            ),
        ) as result_multi_overlap:
            assert result_multi_overlap.success
            assert result_multi_overlap.output_for_node("multiply_two") == 6

        with pytest.raises(
            DagsterExecutionStepNotFoundError,
            match="Step selection refers to unknown step: a",
        ):
            execute_job(
                reconstructable(foo_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=pipeline_result_full.run_id,
                    step_selection=["a", "*add_nums"],
                ),
            )

        with pytest.raises(
            DagsterExecutionStepNotFoundError,
            match="Step selection refers to unknown steps: a, b",
        ):
            execute_job(
                reconstructable(foo_job),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=pipeline_result_full.run_id,
                    step_selection=["a+", "*b"],
                ),
            )
