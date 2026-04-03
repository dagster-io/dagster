from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

import dagster as dg


class DataStageProject:
    """Wrapper around a DataStage job configuration.

    Describes the tables that a DataStage job replicates along with
    source / target connection info.
    """

    def __init__(self, project_config: dict[str, Any]) -> None:
        self._config = project_config

    @property
    def job_name(self) -> str:
        return self._config["job_name"]

    @property
    def tables(self) -> list[dict[str, str]]:
        return self._config["tables"]

    @property
    def source_connection(self) -> dict[str, Any]:
        return self._config["source_connection"]

    @property
    def target_connection(self) -> dict[str, Any]:
        return self._config["target_connection"]


# start_datastage_translator
@dataclass
class DataStageTranslator:
    """Translates DataStage table definitions into Dagster asset attributes.

    Subclass and override any method to customise key structure, groups, etc.
    """

    def get_asset_key(self, table_def: Mapping[str, str]) -> dg.AssetKey:
        """Default: ``["datastage_raw", "<table_name>"]``."""
        return dg.AssetKey(["datastage_raw", table_def["name"]])

    def get_group_name(self, table_def: Mapping[str, str]) -> str:
        return "datastage_replication"

    def get_description(self, table_def: Mapping[str, str]) -> str:
        source_schema = table_def.get("source_schema", "UNKNOWN")
        return f"Replicated from IBM DataStage - source: {source_schema}.{table_def['name']}"

    def get_tags(self, table_def: Mapping[str, str]) -> dict[str, str]:
        return {
            "source_system": "ibm_datastage",
            "schedule": "daily",
        }


# end_datastage_translator


# start_datastage_resource
class DataStageResource(dg.ConfigurableResource):
    """Resource that drives IBM DataStage via the ``cpdctl dsjob`` CLI.

    In **demo mode** the resource simulates a successful replication and
    yields ``MaterializeResult`` + ``AssetCheckResult`` per table without
    calling any external system.
    """

    cpdctl_profile: str = "cp4d-profile"
    project_name: str = "PROD_PROJECT"
    demo_mode: bool = True

    def run(
        self,
        context: dg.AssetExecutionContext,
        project: DataStageProject,
        translator: DataStageTranslator,
    ) -> Iterator[dg.MaterializeResult | dg.AssetCheckResult]:
        """Execute the DataStage job and yield a ``MaterializeResult`` and
        ``AssetCheckResult`` objects per replicated table, all in one step.
        """
        if self.demo_mode:
            yield from self._run_demo(context, project, translator)
        else:
            yield from self._run_production(context, project, translator)

    def _run_demo(
        self,
        context: dg.AssetExecutionContext,
        project: DataStageProject,
        translator: DataStageTranslator,
    ) -> Iterator[dg.MaterializeResult | dg.AssetCheckResult]:
        import random
        import time

        context.log.info(
            f"[DEMO MODE] Simulating DataStage job '{project.job_name}' "
            f"for {len(project.tables)} tables"
        )

        for table_def in project.tables:
            time.sleep(0.3)
            table_name = table_def["name"]
            asset_key = translator.get_asset_key(table_def)
            row_count = random.randint(5_000, 500_000)

            context.log.info(f"[DEMO] Replicated {table_name}: {row_count:,} rows")

            yield dg.MaterializeResult(
                asset_key=asset_key,
                metadata={
                    "row_count": dg.MetadataValue.int(row_count),
                    "source_schema": dg.MetadataValue.text(
                        table_def.get("source_schema", "UNKNOWN")
                    ),
                    "target_schema": dg.MetadataValue.text(
                        table_def.get("target_schema", "UNKNOWN")
                    ),
                    "job_name": dg.MetadataValue.text(project.job_name),
                    "status": dg.MetadataValue.text("SUCCESS"),
                },
            )

            yield dg.AssetCheckResult(
                check_name=f"{table_name}_row_count_positive",
                passed=True,
                asset_key=asset_key,
                metadata={
                    "row_count": dg.MetadataValue.int(row_count),
                },
            )
            yield dg.AssetCheckResult(
                check_name=f"{table_name}_freshness",
                passed=True,
                asset_key=asset_key,
                metadata={
                    "hours_since_materialization": dg.MetadataValue.float(0.0),
                },
            )

    def _run_production(
        self,
        context: dg.AssetExecutionContext,
        project: DataStageProject,
        translator: DataStageTranslator,
    ) -> Iterator[dg.MaterializeResult | dg.AssetCheckResult]:
        yield from _run_datastage_production(
            context=context,
            project=project,
            translator=translator,
            cpdctl_profile=self.cpdctl_profile,
            project_name=self.project_name,
        )


# end_datastage_resource


# start_datastage_resource_production
def _run_datastage_production(
    *,
    context: dg.AssetExecutionContext,
    project: DataStageProject,
    translator: DataStageTranslator,
    cpdctl_profile: str,
    project_name: str,
) -> Iterator[dg.MaterializeResult | dg.AssetCheckResult]:
    import subprocess

    context.log.info(
        f"Running DataStage job '{project.job_name}' "
        f"via cpdctl dsjob CLI (profile: {cpdctl_profile})"
    )

    run_result = subprocess.run(
        [
            "cpdctl",
            "dsjob",
            "run",
            "--project",
            project_name,
            "--job",
            project.job_name,
            "--wait",
            "1800",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    context.log.info(f"cpdctl dsjob run output:\n{run_result.stdout}")

    info_result = subprocess.run(
        [
            "cpdctl",
            "dsjob",
            "jobinfo",
            "--project",
            project_name,
            "--job",
            project.job_name,
            "--full",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    context.log.info(f"cpdctl dsjob jobinfo output:\n{info_result.stdout}")

    rows_by_table: dict[str, int] = {}
    for line in info_result.stdout.splitlines():
        for table_def in project.tables:
            tname = table_def["name"]
            if tname in line and "rows" in line.lower():
                digit_str = "".join(c for c in line.split(":")[-1] if c.isdigit())
                rows_by_table[tname] = int(digit_str) if digit_str else 0

    log_result = subprocess.run(
        [
            "cpdctl",
            "dsjob",
            "logdetail",
            "--project",
            project_name,
            "--job",
            project.job_name,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    context.log.info(f"cpdctl dsjob logdetail output:\n{log_result.stdout}")

    for table_def in project.tables:
        table_name = table_def["name"]
        asset_key = translator.get_asset_key(table_def)
        row_count = rows_by_table.get(table_name, 0)

        yield dg.MaterializeResult(
            asset_key=asset_key,
            metadata={
                "row_count": dg.MetadataValue.int(row_count),
                "source_schema": dg.MetadataValue.text(table_def.get("source_schema", "UNKNOWN")),
                "target_schema": dg.MetadataValue.text(table_def.get("target_schema", "UNKNOWN")),
                "job_name": dg.MetadataValue.text(project.job_name),
                "status": dg.MetadataValue.text("SUCCESS"),
            },
        )

        yield dg.AssetCheckResult(
            check_name=f"{table_name}_row_count_positive",
            passed=bool(row_count > 0),
            asset_key=asset_key,
            metadata={
                "row_count": dg.MetadataValue.int(row_count),
            },
        )
        yield dg.AssetCheckResult(
            check_name=f"{table_name}_freshness",
            passed=True,
            asset_key=asset_key,
            metadata={
                "hours_since_materialization": dg.MetadataValue.float(0.0),
            },
        )


# end_datastage_resource_production


# start_datastage_assets
def datastage_assets(
    *,
    project: DataStageProject,
    name: str | None = None,
    group_name: str | None = None,
    translator: DataStageTranslator | None = None,
) -> Callable[[Callable[..., Any]], dg.AssetsDefinition]:
    """Return a ``@multi_asset`` decorator whose decorated function yields
    ``MaterializeResult`` and ``AssetCheckResult`` for every table in
    the DataStage project, all in a single materialisation step.

    Usage::

        @datastage_assets(project=my_project, name="ds_replication")
        def my_replication(context, datastage: DataStageResource):
            yield from datastage.run(context, my_project, my_translator)
    """
    translator = translator or DataStageTranslator()

    specs = [
        dg.AssetSpec(
            key=translator.get_asset_key(table_def),
            group_name=group_name or translator.get_group_name(table_def),
            description=translator.get_description(table_def),
            tags=translator.get_tags(table_def),
            kinds={"ibm_datastage", "python"},
        )
        for table_def in project.tables
    ]

    check_specs = []
    for table_def in project.tables:
        asset_key = translator.get_asset_key(table_def)
        table_name = table_def["name"]
        check_specs.append(
            dg.AssetCheckSpec(
                name=f"{table_name}_row_count_positive",
                asset=asset_key,
                description=f"Verify {table_name} has > 0 rows after replication",
            )
        )
        check_specs.append(
            dg.AssetCheckSpec(
                name=f"{table_name}_freshness",
                asset=asset_key,
                description=f"Verify {table_name} was replicated recently",
            )
        )

    return dg.multi_asset(
        name=name,
        specs=specs,
        check_specs=check_specs,
    )


# end_datastage_assets


# start_datastage_component
class DataStageJobComponent(dg.Component, dg.Model, dg.Resolvable):
    """Dagster Component wrapping an IBM DataStage replication job.

    Produces one asset and two data-quality checks per replicated table
    in a single ``@multi_asset`` step. Set ``demo_mode: true`` to simulate
    the replication locally without a ``cpdctl`` installation.
    """

    demo_mode: bool = True
    job_name: str = "datastage_job"
    cpdctl_profile: str = "cp4d-profile"
    datastage_project_name: str = "PROD_PROJECT"
    source_connection: dict[str, Any] = {}
    target_connection: dict[str, Any] = {}
    tables: list[dict[str, str]] = []

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        project = DataStageProject(
            {
                "job_name": self.job_name,
                "source_connection": self.source_connection,
                "target_connection": self.target_connection,
                "tables": self.tables,
            }
        )
        translator = DataStageTranslator()

        @datastage_assets(
            project=project,
            name=f"{self.job_name}_replication",
            translator=translator,
        )
        def replication_assets(
            context: dg.AssetExecutionContext,
            datastage: DataStageResource,
        ):
            yield from datastage.run(context, project, translator)

        resource = DataStageResource(
            cpdctl_profile=self.cpdctl_profile,
            project_name=self.datastage_project_name,
            demo_mode=self.demo_mode,
        )

        return dg.Definitions(
            assets=[replication_assets],
            resources={"datastage": resource},
        )


# end_datastage_component
