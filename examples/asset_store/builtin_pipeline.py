from dagster import DagsterInstance, ModeDefinition, execute_pipeline, pipeline, repository, solid
from dagster.core.storage.asset_store import fs_asset_store


def train(df):
    return len(df)


local_asset_store = fs_asset_store.configured({"base_dir": "uncommitted/intermediates/"})


@solid
def call_api(_):
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@solid
def parse_df(context, df):
    context.log.info("{}".format(df))
    result_df = df[:5]
    return result_df


@solid
def train_model(context, df):
    context.log.info("{}".format(df))
    model = train(df)
    return model


@pipeline(
    mode_defs=[
        ModeDefinition("test", resource_defs={"object_manager": fs_asset_store}),
        ModeDefinition("local", resource_defs={"object_manager": local_asset_store}),
    ],
)
def asset_store_pipeline():
    train_model(parse_df(call_api()))


@repository
def asset_store_pipeline_repo():
    return [asset_store_pipeline]


if __name__ == "__main__":
    instance = DagsterInstance.ephemeral()
    result = execute_pipeline(asset_store_pipeline, mode="local", instance=instance)
