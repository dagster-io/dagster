from collections.abc import Sequence

from dagster_components import (
    AssetSpecSchema,
    Component,
    ResolvableSchema,
    registered_component_type,
)


class ShellCommandParams(ResolvableSchema):
    path: str
    asset_specs: Sequence[AssetSpecSchema]


@registered_component_type(name="shell_command")
<<<<<<< HEAD
class ShellCommand(Component): ...
=======
class ShellCommand(Component):
    def __init__(self, params):
        self.params = params

    ...

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        # highlight-start
        # resolve the script runner with its required additional scope
        script_runner = self.params.resolve(
            load_context.templated_value_resolver.with_scope(
                get_script_runner=_get_script_runner
            )
        )["script_runner"]
        # highlight-end
        ...
        return dg.Definitions(...)
>>>>>>> b1f485c0cd ([dg docs] Add docs e2e test, screenshot generation for component type tutorial)
