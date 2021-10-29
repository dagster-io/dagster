from dagster import repository

from .jobs.hacker_news_api_download import hacker_news_api_download
from .jobs.story_recommender import story_recommender


@repository
def hacker_news_repository():
    return [
        hacker_news_api_download,
        # story_recommender,
    ]
