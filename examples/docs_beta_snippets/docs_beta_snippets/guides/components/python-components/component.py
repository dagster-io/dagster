from dagster_components import ComponentLoadContext, DbtProjectComponent, component
from dagster_dbt import DagsterDbtTranslator, DbtCliResource


class MyTranslator(DagsterDbtTranslator): ...


@component
def my_dbt_component(context: ComponentLoadContext) -> DbtProjectComponent:
    return DbtProjectComponent(
        dbt=DbtCliResource(project_dir="."),
        translator=MyTranslator(),
    )
