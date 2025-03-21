from dagster_components import DefsLoadContext, component
from dagster_components.dagster_dbt import DbtProjectComponent
from dagster_dbt import DagsterDbtTranslator, DbtCliResource


class MyTranslator(DagsterDbtTranslator): ...


@component
def my_dbt_component(context: DefsLoadContext) -> DbtProjectComponent:
    return DbtProjectComponent(
        dbt=DbtCliResource(project_dir="."),
        translator=MyTranslator(),
    )
