from dagster import ModeDefinition, ResourceDefinition, pipeline
from hacker_news.ops.comment_stories import build_comment_stories
from hacker_news.ops.recommender_model import (
    build_component_top_stories,
    build_recommender_model,
    model_perf_notebook,
)
from hacker_news.ops.user_story_matrix import build_user_story_matrix
from hacker_news.ops.user_top_recommended_stories import build_user_top_recommended_stories
from hacker_news.resources import RESOURCES_LOCAL, RESOURCES_PROD
from hacker_news.resources.snowflake_io_manager import snowflake_io_manager

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
    resource_defs=dict(
        **RESOURCES_LOCAL,
        **{"partition_bounds": ResourceDefinition.none_resource()},
    ),
)

PROD_MODE = ModeDefinition(
    "prod",
    description="This mode writes some outputs to the production data warehouse.",
    resource_defs=dict(
        **RESOURCES_PROD,
        **{"partition_bounds": ResourceDefinition.none_resource()},
    ),
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
