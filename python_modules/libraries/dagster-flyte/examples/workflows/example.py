import sys

from dagster_flyte import compile_pipeline_to_flyte  # pylint: disable=import-error
from flytekit.common.tasks import sdk_runnable
from flytekit.common.workflow import SdkWorkflow

from dagster import pipeline, solid


@solid
def mult_x(context, x):  # pylint: disable=unused-argument
    return 2 * x


@pipeline
def pipe():
    mult_x()


environment_dict: dict = {'solids': {'mult_x': {'inputs': {'x': {'value': 2}}}}}

workflow_obj = compile_pipeline_to_flyte(pipe, environment_dict=environment_dict, module=__name__)

assert isinstance(workflow_obj, SdkWorkflow)
assert len(workflow_obj.nodes) == 1
assert hasattr(sys.modules[__name__], 'mult_x')
assert isinstance(getattr(sys.modules[__name__], 'mult_x'), sdk_runnable.SdkRunnableTask)
