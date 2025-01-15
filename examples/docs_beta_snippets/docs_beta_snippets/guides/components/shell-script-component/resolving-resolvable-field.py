from dagster_components import Component, ComponentLoadContext, component_type

import dagster as dg


class ScriptRunner: ...


def _get_script_runner(val: str) -> ScriptRunner:
    return ScriptRunner()


@component_type(name="shell_command")
class ShellCommand(Component):
    def __init__(self, params):
        self.params = params

    ...

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        # highlight-start
        # resolve the script runner with its required additional scope
        script_runner = self.params.resolve_properties(
            load_context.templated_value_resolver.with_scope(
                get_script_runner=_get_script_runner
            )
        )["script_runner"]
        # highlight-end
        ...
        return dg.Definitions(...)
