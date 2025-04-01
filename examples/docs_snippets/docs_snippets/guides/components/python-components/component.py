from dagster_components import component
from dagster_components.core.context import ComponentLoadContext
from dagster_components.dagster_dbt import DbtProjectComponent
from dagster_dbt import DagsterDbtTranslator, DbtCliResource


class MyTranslator(DagsterDbtTranslator): ...


@component
def my_dbt_component(context: ComponentLoadContext) -> DbtProjectComponent:
    return DbtProjectComponent(
        dbt=DbtCliResource(project_dir="."),
        translator=MyTranslator(),
    )
