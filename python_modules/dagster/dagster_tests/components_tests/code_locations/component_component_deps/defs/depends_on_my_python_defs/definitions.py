import dagster as dg
from dagster.components.core.context import ComponentLoadContext
from dagster_shared import check


@dg.definitions
def defs(context: ComponentLoadContext) -> dg.Definitions:
    from component_component_deps.defs import my_python_defs  # type:ignore

    @dg.asset(
        deps=check.is_list(context.load_defs(my_python_defs).assets, of_type=dg.AssetsDefinition)
    )
    def downstream_of_all_my_python_defs(): ...

    return dg.Definitions(assets=[downstream_of_all_my_python_defs])
