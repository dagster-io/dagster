from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable, Optional, Union

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster_components import ComponentLoadContext
from dagster_components.components.step.step import AssetGraphStep, step
from dagster_components.core.component import Component, loader


def execute_asset_component(
    loader: Callable[[ComponentLoadContext], Component],
) -> ExecuteInProcessResult:
    component_load_context = ComponentLoadContext.for_test()
    component = loader(component_load_context)
    defs = component.build_defs(context=component_load_context)

    asset_key = next(iter(defs.get_asset_graph().get_all_asset_keys()))
    assets_def = defs.get_assets_def(asset_key)
    return materialize([assets_def])


def test_hello_world() -> None:
    def execute(context) -> MaterializeResult:
        return MaterializeResult()

    @loader
    def load(context: ComponentLoadContext) -> AssetGraphStep:
        return AssetGraphStep(
            name="step",
            fn=execute,
            assets=[AssetSpec(key="asset_one")],
        )

    result = execute_asset_component(load)
    assert result.success


def test_hello_world_decorator() -> None:
    @step(name="the_step", assets=[AssetSpec("the_key")])
    def the_step(context):
        return MaterializeResult()

    result = execute_asset_component(the_step)
    assert result.success


def test_hello_world_graph_asset() -> None:
    @dataclass
    class StepSpec:
        key: str

    class StepGraph(Component):
        @classmethod
        def step(cls, spec: StepSpec, deps: Optional[Sequence[Union[str, StepSpec]]] = None):
            def inner_(fn):
                return fn

            return inner_

        def build_defs(self, context): ...

    class SpecificStepGraph(StepGraph):
        @StepGraph.step(spec=StepSpec("step_one"))
        def step_one(self, context): ...

        @StepGraph.step(spec=StepSpec("step_two"), deps=["step_one"])
        def step_two(self, context): ...

    @loader
    def load(context):
        return SpecificStepGraph()
