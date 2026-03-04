"""Scaffolder for Spark Declarative Pipeline component."""

from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest


class SparkDeclarativePipelineScaffolder(Scaffolder):
    """Scaffolds a Spark Declarative Pipeline component defs.yaml and pipeline spec path."""

    def scaffold(self, request: ScaffoldRequest) -> None:
        scaffold_component(
            request,
            {
                "pipeline_spec_path": "spark-pipeline.yml",
                "discovery_mode": "dry_run_only",
            },
        )
