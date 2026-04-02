import dagster as dg


def process_file(file_path: str): ...


@dg.asset(
    deps=["raw_data"],
    automation_condition=dg.AutomationCondition.eager(),
)
def processed_data(context: dg.AssetExecutionContext):
    instance = context.instance
    event = instance.get_latest_materialization_event(dg.AssetKey("raw_data"))
    metadata = event.asset_materialization.metadata
    file_path = metadata["file_path"].value
    return process_file(file_path)
