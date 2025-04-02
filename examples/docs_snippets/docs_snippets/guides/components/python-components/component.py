from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProjectComponent

from dagster.components import ComponentLoadContext, component


class MyTranslator(DagsterDbtTranslator): ...


@component
def my_dbt_component(context: ComponentLoadContext) -> DbtProjectComponent:
    return DbtProjectComponent(
        dbt=DbtCliResource(project_dir="."),
        translator=MyTranslator(),
    )
