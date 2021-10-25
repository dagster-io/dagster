from dagster import ResourceDefinition, graph
from dagstermill.io_managers import local_output_notebook_io_manager
from hacker_news.ops.comment_stories import build_comment_stories
from hacker_news.ops.recommender_model import (
    build_component_top_stories,
    build_recommender_model,
    model_perf_notebook,
)
from hacker_news.ops.user_story_matrix import build_user_story_matrix
from hacker_news.ops.user_top_recommended_stories import build_user_top_recommended_stories
from hacker_news.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from hacker_news.resources.s3_notebook_io_manager import s3_notebook_io_manager

STORY_RECOMMENDER_RESOURCES_LOCAL = {
    **RESOURCES_LOCAL,
    **{
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "partition_start": ResourceDefinition.none_resource(),
        "partition_end": ResourceDefinition.none_resource(),
    },
}

STORY_RECOMMENDER_RESOURCES_STAGING = dict(
    **RESOURCES_STAGING,
    **{
        "output_notebook_io_manager": s3_notebook_io_manager,
        "partition_start": ResourceDefinition.none_resource(),
        "partition_end": ResourceDefinition.none_resource(),
    },
)

STORY_RECOMMENDER_RESOURCES_PROD = dict(
    **RESOURCES_PROD,
    **{
        "output_notebook_io_manager": s3_notebook_io_manager,
        "partition_start": ResourceDefinition.none_resource(),
        "partition_end": ResourceDefinition.none_resource(),
    },
)


@graph
def story_recommender():
    """
    Trains a collaborative filtering model that can recommend HN stories to users based on what
    stories they've commented on in the past.
    """
    comment_stories = build_comment_stories()
    user_story_matrix = build_user_story_matrix(comment_stories)
    recommender_model = build_recommender_model(user_story_matrix)
    model_perf_notebook(recommender_model)
    build_component_top_stories(recommender_model, user_story_matrix)
    build_user_top_recommended_stories(recommender_model, user_story_matrix)


story_recommender_prod_job = story_recommender.to_job(
    resource_defs=STORY_RECOMMENDER_RESOURCES_PROD
)

story_recommender_staging_job = story_recommender.to_job(
    resource_defs=STORY_RECOMMENDER_RESOURCES_STAGING
)

story_recommender_local_job = story_recommender.to_job(
    resource_defs=STORY_RECOMMENDER_RESOURCES_LOCAL
)
