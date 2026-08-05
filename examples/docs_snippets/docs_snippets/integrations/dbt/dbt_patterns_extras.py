# ruff: noqa
from typing import Any, Mapping, Optional

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

# Replace with your project's manifest path.
MANIFEST_PATH = ""


# start_grouping_translator
class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        # Group by model directory.
        model_path = dbt_resource_props.get("original_file_path", "")
        if "marts/" in model_path:
            return "marts"
        if "staging/" in model_path:
            return "staging"
        if "intermediate/" in model_path:
            return "intermediate"

        # Group by tag.
        tags = dbt_resource_props.get("tags", [])
        if "finance" in tags:
            return "finance"
        if "marketing" in tags:
            return "marketing"

        # Group by meta config.
        meta = dbt_resource_props.get("config", {}).get("meta", {})
        if "dagster_group" in meta:
            return meta["dagster_group"]

        return "dbt_models"


@dbt_assets(
    manifest=MANIFEST_PATH,
    dagster_dbt_translator=CustomDagsterDbtTranslator(),
)
def grouped_dbt_assets(context: dg.AssetExecutionContext, dbt_cli: DbtCliResource):
    yield from dbt_cli.cli(["build"], context=context).stream()


# end_grouping_translator


# start_tagged_tests
@dg.op(required_resource_keys={"dbt"})
def run_tagged_tests(context):
    """Run only tests with specific tags using the dbt CLI directly."""
    dbt = context.resources.dbt
    return dbt.cli(["test", "--select", "tag:hourly_tests"], context=context)


@dg.job(resource_defs={"dbt": DbtCliResource(project_dir="path/to/dbt")})
def hourly_tests_job():
    run_tagged_tests()


hourly_test_schedule = dg.ScheduleDefinition(
    name="hourly_tests_schedule",
    cron_schedule="0 * * * *",
    job=hourly_tests_job,
    execution_timezone="UTC",
)
# end_tagged_tests
