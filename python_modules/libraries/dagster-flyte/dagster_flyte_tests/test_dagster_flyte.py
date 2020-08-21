import sys

import pytest
from dagster_flyte import compile_pipeline_to_flyte
from flytekit.common.tasks import sdk_runnable
from flytekit.common.workflow import SdkWorkflow

from dagster import pipeline, solid


def test_flyte_sdk_workflow():
    @solid
    def mult_x(_, x: int) -> int:
        return 2 * x

    @pipeline
    def pipe():
        mult_x()

    run_config = {
        "storage": {"filesystem": {}},
        "solids": {"mult_x": {"inputs": {"x": {"value": 2}}}},
    }

    workflow_obj = compile_pipeline_to_flyte(pipe, run_config=run_config, module=__name__)

    assert isinstance(workflow_obj, SdkWorkflow)
    assert len(workflow_obj.nodes) == 1
    assert hasattr(sys.modules[__name__], "mult_x")
    assert isinstance(getattr(sys.modules[__name__], "mult_x"), sdk_runnable.SdkRunnableTask)


def test_workflow_with_any_type():
    @solid
    def mult_x(_, x):
        return 2 * x

    @pipeline
    def pipe():
        mult_x()

    run_config = {
        "storage": {"filesystem": {}},
        "solids": {"mult_x": {"inputs": {"x": {"value": 2}}}},
    }

    with pytest.raises(TypeError):
        compile_pipeline_to_flyte(pipe, run_config=run_config, module=__name__)


def test_multi_step_pipeline():
    @solid
    def mult_x(_, x: int) -> int:
        return 2 * x

    @solid
    def add(_, to_sum: int, y: int) -> int:
        return to_sum + y

    @pipeline
    def pipe():
        add(mult_x())

    run_config = {
        "storage": {"filesystem": {}},
        "solids": {
            "mult_x": {"inputs": {"x": {"value": 2}}},
            "add": {"inputs": {"y": {"value": 3}}},
        },
    }

    workflow_obj = compile_pipeline_to_flyte(pipe, run_config=run_config, module=__name__)

    assert isinstance(workflow_obj, SdkWorkflow)
    assert len(workflow_obj.nodes) == 2
    assert hasattr(sys.modules[__name__], "mult_x")
    assert hasattr(sys.modules[__name__], "add")
    assert isinstance(getattr(sys.modules[__name__], "mult_x"), sdk_runnable.SdkRunnableTask)
    assert isinstance(getattr(sys.modules[__name__], "add"), sdk_runnable.SdkRunnableTask)


def test_multi_step_from_multi_outputs():
    @solid
    def mult_x(_, x: int) -> int:
        return 2 * x

    @solid
    def add(_, to_sum: list) -> int:
        return to_sum[0] + to_sum[1]

    @solid
    def add_z(_, z: int) -> int:
        return 3 * z

    @pipeline
    def pipe():
        summed = mult_x()
        added = add_z()
        result = add(to_sum=[summed, added])
        return result

    run_config = {
        "storage": {"filesystem": {}},
        "solids": {
            "mult_x": {"inputs": {"x": {"value": 2}}},
            "add_z": {"inputs": {"z": {"value": 3}}},
        },
    }

    workflow_obj = compile_pipeline_to_flyte(pipe, run_config=run_config, module=__name__)

    assert isinstance(workflow_obj, SdkWorkflow)
    assert len(workflow_obj.nodes) == 3
    assert hasattr(sys.modules[__name__], "mult_x")
    assert hasattr(sys.modules[__name__], "add")
    assert hasattr(sys.modules[__name__], "add_z")
    assert isinstance(getattr(sys.modules[__name__], "mult_x"), sdk_runnable.SdkRunnableTask)
    assert isinstance(getattr(sys.modules[__name__], "add"), sdk_runnable.SdkRunnableTask)
    assert isinstance(getattr(sys.modules[__name__], "add_z"), sdk_runnable.SdkRunnableTask)
