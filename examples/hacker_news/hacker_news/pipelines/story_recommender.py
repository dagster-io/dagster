from dagster import ModeDefinition, fs_io_manager, pipeline
from dagster.core.storage.file_manager import local_file_manager
from dagster_aws.s3 import s3_file_manager
from hacker_news.resources.fixed_s3_pickle_io_manager import fixed_s3_pickle_io_manager
from hacker_news.resources.snowflake_io_manager import snowflake_io_manager
from hacker_news.solids.comment_stories import build_comment_stories
from hacker_news.solids.recommender_model import (
    build_component_top_stories,
    build_recommender_model,
    model_perf_notebook,
)
from hacker_news.solids.user_story_matrix import build_user_story_matrix
from hacker_news.solids.user_top_recommended_stories import build_user_top_recommended_stories

snowflake_manager = snowflake_io_manager.configured(
    {
        "account": {"env": "SNOWFLAKE_ACCOUNT"},
        "user": {"env": "SNOWFLAKE_USER"},
        "password": {"env": "SNOWFLAKE_PASSWORD"},
        "database": "DEMO_DB",
        "warehouse": "TINY_WAREHOUSE",
    }
)

DEV_MODE = ModeDefinition(
    "dev",
    description="This mode reads from the same warehouse as the prod pipeline, but does all writes locally.",
    resource_defs={
        "io_manager": fs_io_manager,
        "warehouse_io_manager": fs_io_manager,
        "warehouse_loader": snowflake_manager,
        "file_manager": local_file_manager,
    },
)

PROD_MODE = ModeDefinition(
    "prod",
    description="This mode writes some outputs to the production data warehouse.",
    resource_defs={
        "io_manager": fixed_s3_pickle_io_manager.configured({"bucket": "hackernews-elementl-prod"}),
        "warehouse_io_manager": snowflake_manager,
        "warehouse_loader": snowflake_manager,
        "file_manager": s3_file_manager.configured({"s3_bucket": "hackernews-elementl-prod"}),
    },
)


@pipeline(
    mode_defs=[DEV_MODE, PROD_MODE],
    description="""
    Trains a collaborative filtering model that can recommend HN stories to users based on what
    stories they've commented on in the past.
    """,
)
def story_recommender():
    comment_stories = build_comment_stories()
    user_story_matrix = build_user_story_matrix(comment_stories)
    recommender_model = build_recommender_model(user_story_matrix)
    model_perf_notebook(recommender_model)
    build_component_top_stories(recommender_model, user_story_matrix)
    build_user_top_recommended_stories(recommender_model, user_story_matrix)
