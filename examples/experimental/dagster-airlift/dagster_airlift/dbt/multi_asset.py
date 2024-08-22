from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from dagster import AssetExecutionContext, AssetSpec, Definitions, multi_asset
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    DbtProject,
    build_dbt_asset_specs,
    dbt_assets,
)
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest

from dagster_airlift.core import DefsFactory
from dagster_airlift.core.utils import DAG_ID_TAG, TASK_ID_TAG


@dataclass
class DbtProjectDefs(DefsFactory):
    """A factory that builds a :py:class:`dagster.Definitions` object from a dbt project.
    If the dbt project is not living within the dagster codebase and/or the dbt project is not
    being orchestrated by dagster, just provide a reference to the manifest and external assets
    will be constructed.

    Args:
        dbt_manifest (DbtManifestParam): The dbt manifest. This can be a path to a manifest file,
            a string of the manifest JSON, or the parsed manifest JSON.
        dbt_project_path (Path): The path to the dbt project.
        name (str): The name to give the dbt project. In the case of airflow-orchestrated DBT assets,
            this should be <dag_id>__<task_id>.
        group (Optional[str], optional): The asset group name for the dbt assets. Default is "default".
    """

    dbt_manifest: Mapping[str, Any]
    name: str
    translator: Optional[DagsterDbtTranslator]
    select: str
    exclude: Optional[str]
    project: Optional[DbtProject]

    def __init__(
        self,
        dbt_manifest: DbtManifestParam,
        name: str,
        translator: Optional[DagsterDbtTranslator] = None,
        select: str = "fqn:*",
        exclude: Optional[str] = None,
        project: Optional[DbtProject] = None,
    ):
        self.dbt_manifest = validate_manifest(dbt_manifest)
        self.name = name
        self.translator = translator
        self.select = select
        self.exclude = exclude
        self.project = project

    def build_defs(self) -> Definitions:
        if self.project is None:

            @multi_asset(
                name=self.name,
                specs=build_dbt_asset_specs(
                    manifest=self.dbt_manifest,
                    dagster_dbt_translator=self.translator,
                    select=self.select,
                    exclude=self.exclude,
                    project=self.project,
                ),
            )
            def _multi_asset():
                raise Exception("This should never be called")

            return Definitions(
                assets=[_multi_asset],
            )
        else:

            @dbt_assets(
                manifest=self.dbt_manifest,
                name=self.name,
                project=self.project,
                dagster_dbt_translator=self.translator,
                select=self.select,
                exclude=self.exclude,
            )
            def _dbt_asset(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(["build"], context=context).stream()

            return Definitions(
                assets=[_dbt_asset],
                resources={"dbt": DbtCliResource(project_dir=self.project)},
            )


def specs_from_airflow_dbt(
    *, dag_id: str, task_id: str, manifest: DbtManifestParam
) -> Sequence[AssetSpec]:
    return [
        AssetSpec(
            key=spec.key,
            tags={
                DAG_ID_TAG: dag_id,
                TASK_ID_TAG: task_id,
                **spec.tags,
            },
            deps=spec.deps,
            metadata=spec.metadata,
            description=spec.description,
        )
        for spec in build_dbt_asset_specs(
            manifest=manifest,
        )
    ]


def defs_from_airflow_dbt(
    *,
    dag_id: str,
    task_id: str,
    manifest: DbtManifestParam,
    project: DbtProject,
) -> Definitions:
    @dbt_assets(
        manifest=manifest,
        project=project,
        op_tags={DAG_ID_TAG: dag_id, TASK_ID_TAG: task_id},
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_asset_checks=False)
        ),
    )
    def _dbt_asset(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    return Definitions(
        assets=[_dbt_asset],
        resources={"dbt": DbtCliResource(project_dir=project)},
    )
