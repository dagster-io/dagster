from dagster import pipeline, solid
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.memoization import output_handles_from_execution_plan
from dagster.core.execution.plan.objects import StepOutputHandle


def define_pipeline():
    @solid
    def add_one(_context, num):
        return num + 1

    @solid
    def add_two(_context, num):
        return num + 2

    @solid
    def add_three(_context, num):
        return num + 3

    @pipeline
    def addy_pipeline():
        add_three(add_two(add_one()))

    return addy_pipeline


def test_output_handles_from_execution_plan():
    execution_plan = create_execution_plan(
        define_pipeline(), run_config={"solids": {"add_one": {"inputs": {"num": {"value": 3}}}}},
    )

    assert output_handles_from_execution_plan(execution_plan) == set()
    assert output_handles_from_execution_plan(
        execution_plan.build_subset_plan(["add_two.compute", "add_three.compute"])
    ) == {StepOutputHandle("add_one.compute", "result")}
    assert output_handles_from_execution_plan(
        execution_plan.build_subset_plan(["add_three.compute"])
    ) == {StepOutputHandle("add_two.compute", "result")}
