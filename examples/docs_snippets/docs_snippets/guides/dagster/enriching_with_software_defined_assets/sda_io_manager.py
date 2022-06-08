from pandas import DataFrame

from dagster import SourceAsset, asset, define_asset_job, repository, with_resources

from .mylib import s3_io_manager, snowflake_io_manager, train_recommender_model

raw_users = SourceAsset(key="raw_users", io_manager_key="warehouse")


@asset(io_manager_key="warehouse")
def users(raw_users: DataFrame) -> DataFrame:
    users_df = raw_users.dropna()
    return users_df


@asset(io_manager_key="object_store")
def user_recommender_model(users: DataFrame):
    users_recommender_model = train_recommender_model(users)
    return users_recommender_model


@repository
def repo():
    return [
        *with_resources(
            [raw_users, users, user_recommender_model],
            resource_defs={
                "warehouse": snowflake_io_manager,
                "object_store": s3_io_manager,
            },
        ),
        define_asset_job("users_recommender_job"),
    ]
