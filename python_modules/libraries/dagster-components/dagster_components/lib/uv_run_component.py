from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient

from dagster_components.core.component import component_type
from dagster_components.lib.native_step_component import NativeStepComponent


@component_type(name="uv_run")
class UvRunComponent(NativeStepComponent):
    def execute(self, context: AssetExecutionContext):
        client = PipesSubprocessClient()
        invocation = client.run(context=context, command=["uv", "run", str(self.script_path)])
        return invocation.get_results()
