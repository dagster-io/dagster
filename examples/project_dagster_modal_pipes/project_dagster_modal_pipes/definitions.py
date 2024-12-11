"""Poll podcast feeds, and e-mail summaries.

USAGE

    Ensure the following environment variables have been set

        CLOUDFLARE_R2_API
        CLOUDFLARE_R2_ACCESS_KEY_ID
        CLOUDFLARE_R2_SECRET_ACCESS_KEY
        OPENAI_API_KEY
        GMAIL_USER
        GMAIL_APP_PASSWORD
        SUMMARY_RECIPIENT_EMAIL

    Run Dagster

        dagster dev

"""

import dagster as dg

from project_dagster_modal_pipes.pipeline_factory import RSSFeedDefinition, rss_pipeline_factory
from project_dagster_modal_pipes.resources import modal_resource, openai_resource, s3_resource

feeds = [
    RSSFeedDefinition(
        name="practical_ai",
        url="https://changelog.com/practicalai/feed",
    ),
    RSSFeedDefinition(
        name="comedy_bang_bang",
        url="https://feeds.simplecast.com/byb4nhvN",
    ),
    RSSFeedDefinition(
        name="talk_tuah",
        url="https://feeds.simplecast.com/lHFdU_33",
    ),
]

pipeline_definitions = [rss_pipeline_factory(feed) for feed in feeds]


defs = dg.Definitions.merge(
    *pipeline_definitions,
    dg.Definitions(
        resources={
            "s3": s3_resource,
            "modal": modal_resource,
            "openai": openai_resource,
        }
    ),
)
