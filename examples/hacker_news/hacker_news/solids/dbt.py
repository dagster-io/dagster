from dagster import Output, OutputDefinition, solid
from dagster_dbt import DbtCliOutput


@solid(
    required_resource_keys={"dbt", "run_date", "dbt_assets"},
    output_defs=[OutputDefinition(dagster_type=DbtCliOutput)],
    tags={"kind": "dbt"},
)
def hn_dbt_run(context):
    dbt_cli_output = context.resources.dbt.run(vars={"run_date": context.resources.run_date})
    # here, we use a resource to determine which AssetMaterialization events to yield for
    # a given DbtCliOutput. This is done so we can swap out this implementation between modes,
    # as dbt will output to different locations depending on which profile is being used.

    # if you don't use the Dagster Asset Catalog, this can be omitted.
    for materialization in context.resources.dbt_assets.get_asset_materializations(dbt_cli_output):
        yield materialization
    yield Output(dbt_cli_output)


@solid(required_resource_keys={"dbt"}, tags={"kind": "dbt"})
def hn_dbt_test(context, _dbt_output):
    context.resources.dbt.test()
