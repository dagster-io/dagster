# start_repo_marker_0
from dagster import (
    AssetKey,
    AssetMaterialization,
    EventMetadataEntry,
    Field,
    Output,
    pipeline,
    repository,
    solid,
)


@solid(config_schema={"num": Field(float, is_required=False, default_value=1.0)})
def source_float(context):
    return context.solid_config["num"]


@solid
def add_one_and_materialize(_, num):
    result = num + 1
    yield AssetMaterialization(
        description="Analytics dashboard for example pipeline",
        asset_key=AssetKey(["dashboards", "analytics_dashboard"]),
        metadata_entries=[
            EventMetadataEntry.url(
                "http://mycoolwebsite.com/dashboards/analytics", "dashboard url"
            ),
            EventMetadataEntry.float(result, "numeric value"),
        ],
    )

    # Because we are yielding a materialization event as well as an output, we need to explicitly
    # yield an `Output` instead of relying on the return value of the solid
    yield Output(result)


@pipeline
def materialization_pipeline():
    add_one_and_materialize(source_float())


@repository
def materializations_example_repo():
    return [materialization_pipeline]


# end_repo_marker_0
