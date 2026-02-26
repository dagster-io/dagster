from collections.abc import Iterable

import dagster as dg
from dagster.components.lib.executable_component.component import ExecutableComponent
from dagster.components.resolved.core_models import OpSpec


class MyExecutableComponent(ExecutableComponent):
    def invoke_execute_fn(
        self,
        context: dg.AssetExecutionContext | dg.AssetCheckExecutionContext,
        component_load_context: dg.ComponentLoadContext,
    ) -> Iterable:
        return []

    @property
    def op_spec(self) -> OpSpec:
        return OpSpec(name="my_executable_component")
