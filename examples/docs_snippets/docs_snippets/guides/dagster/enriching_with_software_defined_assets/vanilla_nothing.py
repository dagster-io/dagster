from pandas import read_sql

from dagster import Definitions, In, Nothing, job, op

from .mylib import create_db_connection, pickle_to_s3, train_recommender_model


@op
def build_users():
    raw_users_df = read_sql("select * from raw_users", con=create_db_connection())
    users_df = raw_users_df.dropna()
    users_df.to_sql(name="users", con=create_db_connection())


@op(ins={"users": In(Nothing)})
def build_user_recommender_model():
    users_df = read_sql("select * from users", con=create_db_connection())
    users_recommender_model = train_recommender_model(users_df)
    pickle_to_s3(users_recommender_model, key="users_recommender_model")


@job
def users_recommender_job():
    build_user_recommender_model(build_users())


defs = Definitions(
    jobs=[users_recommender_job],
)
