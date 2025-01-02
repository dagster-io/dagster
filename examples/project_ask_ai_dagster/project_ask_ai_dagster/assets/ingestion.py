import dagster as dg
from project_ask_ai_dagster.resources.github import GithubResource
from project_ask_ai_dagster.resources.openai import RateLimitedOpenAIEmbeddingsResource
from project_ask_ai_dagster.resources.scraper import scraper_resource

START_TIME = "2023-01-01"
daily_partition = dg.DailyPartitionsDefinition(start_date=START_TIME)

url_partition = dg.DynamicPartitionsDefinition()

def get_sitemap(scraper_resource) -> List[str]:
    return scraper_resource.parse_sitemap()


@dg.asset(
    group_name="ingestion",
    kinds={"github","python"},
    partitions_def=daily_partition,
)
def github_data(context: dg.AssetExecutionContext,
                    github: GithubResource,
                    open_ai: RateLimitedOpenAIEmbeddingsResource) -> dg.MaterializeResult:
    """Fetch Github Issues and Discussions and feed into Chroma db.

    Since the Github API limits search results to 1000, we partition by updated at
    month, which should be enough to get all the issues and discussions. We use
    updated_at to ensure we don't miss any issues that are updated after the
    partition month. The underlying auto-materialize policy runs this asset every
    day to refresh all data for the current month.
    """
    start, end = context.partition_time_window
    context.log.info(f"Finding issues from {start} to {end}")

    issues = github.get_issues(start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))
    discussions = github.get_discussions(start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))

    issue_docs = github._convert_issues_to_documents(issues)
    discussion_docs = github._convert_discussions_to_documents(discussions)

    open_ai.process_documents(issue_docs + discussion_docs)
    
    return dg.MaterializeResult(
        metadata={
            "number_of_issues": len(issues),
            "number_of_discussions": len(discussions),
        }
    )

dg.asset(
    group_name="ingestion",
    kinds={"webscraping","python"},
    partitions_def=url_partition
)
def docs_scraping(context: dg.AssetExecutionContext):

    return dg.MaterializeResult(
        metadata={
            "number_of_issues": len(issues),
            "number_of_discussions": len(discussions),
        }
    )