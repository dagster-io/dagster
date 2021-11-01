from dagster import ResourceDefinition, graph
from hacker_news.ops.comment_stories import build_comment_stories
from hacker_news.ops.recommender_model import (
    build_component_top_stories,
    build_recommender_model,
    model_perf_notebook,
)
from hacker_news.ops.user_story_matrix import build_user_story_matrix
from hacker_news.ops.user_top_recommended_stories import build_user_top_recommended_stories
from hacker_news.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING


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
    resource_defs=dict(
        **RESOURCES_PROD,
        **{"partition_bounds": ResourceDefinition.none_resource()},
    )
)

story_recommender_staging_job = story_recommender.to_job(
    resource_defs=dict(
        **RESOURCES_STAGING,
        **{"partition_bounds": ResourceDefinition.none_resource()},
    )
)

story_recommender_local_job = story_recommender.to_job(
    resource_defs=dict(
        **RESOURCES_LOCAL,
        **{"partition_bounds": ResourceDefinition.none_resource()},
    )
)
