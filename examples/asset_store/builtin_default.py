from dagster import (
    DagsterInstance,
    ModeDefinition,
    OutputDefinition,
    PresetDefinition,
    execute_pipeline,
    pipeline,
    repository,
    solid,
)
from dagster.core.storage.asset_store import default_filesystem_asset_store


def train(df):
    return len(df)


local_asset_store = default_filesystem_asset_store.configured(
    {"base_dir": "uncommitted/intermediates/"}
)


@solid(output_defs=[OutputDefinition(asset_store_key="fs_asset_store")])
def call_api(_):
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@solid(output_defs=[OutputDefinition(asset_store_key="fs_asset_store")])
def parse_df(context, df):
    context.log.info("{}".format(df))
    result_df = df[:5]
    return result_df


@solid(output_defs=[OutputDefinition(asset_store_key="fs_asset_store")])
def train_model(context, df):
    context.log.info("{}".format(df))
    model = train(df)
    return model


@pipeline(
    mode_defs=[
        ModeDefinition("test", resource_defs={"fs_asset_store": default_filesystem_asset_store}),
        ModeDefinition("local", resource_defs={"fs_asset_store": local_asset_store}),
    ],
    preset_defs=[
        PresetDefinition("local", run_config={"storage": {"filesystem": {}}}, mode="local"),
    ],
)
def model_pipeline():
    train_model(parse_df(call_api()))


@repository
def builtin_default_repo():
    return [model_pipeline]


if __name__ == "__main__":
    instance = DagsterInstance.ephemeral()
    result = execute_pipeline(model_pipeline, preset="local", instance=instance)
