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

        dg dev

"""

import dagster as dg

# start_factory
from project_dagster_modal_pipes.defs.pipeline_factory import (
    RSSFeedDefinition,
    rss_pipeline_factory,
)

# end_factory


# start_def
@dg.definitions
def defs() -> dg.Definitions:
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
    return dg.Definitions.merge(*[rss_pipeline_factory(feed) for feed in feeds])


# end_def
