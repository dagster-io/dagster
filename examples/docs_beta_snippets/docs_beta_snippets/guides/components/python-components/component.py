from dagster_components import ComponentLoadContext, defs_module
from dagster_components.dagster_dbt import DbtProjectComponent
from dagster_dbt import DagsterDbtTranslator, DbtCliResource


class MyTranslator(DagsterDbtTranslator): ...


@defs_module
def my_dbt_component(context: ComponentLoadContext) -> DbtProjectComponent:
    return DbtProjectComponent(
        dbt=DbtCliResource(project_dir="."),
        translator=MyTranslator(),
    )
