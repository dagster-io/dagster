from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster_embedded_elt.sling.resources import AssetExecutionContext

from dagster_components.core.component import component
from dagster_components.lib.native_step_component import NativeStepComponent


@component(name="uv_run")
class UnRunComponent(NativeStepComponent):
    def execute(self, context: AssetExecutionContext):
        # Do the thing
        client = PipesSubprocessClient()
        invocation = client.run(context=context, command=["uv", "run", "step.py"])
        return invocation.get_results()
