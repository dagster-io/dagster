import hashlib

import dagster as dg

from project_ask_ai_dagster.resources.github import GithubResource
from project_ask_ai_dagster.resources.pinecone import PineconeResource
from project_ask_ai_dagster.resources.scraper import SitemapScraper, scraper_resource

START_TIME = "2023-01-01"
daily_partition = dg.WeeklyPartitionsDefinition(start_date=START_TIME)


@dg.asset(
    group_name="ingestion",
    kinds={"github", "Pinecone", "openai"},
    partitions_def=daily_partition,
    automation_condition=dg.AutomationCondition.on_cron("@daily"),
)
def github_issues(
    context: dg.AssetExecutionContext,
    github: GithubResource,
    pinecone: PineconeResource,
) -> dg.MaterializeResult:
    start, end = context.partition_time_window
    context.log.info(f"Finding issues from {start} to {end}")

    issues = github.get_issues(
        start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d")
    )

    issue_docs = github.convert_issues_to_documents(issues)

    # Create index if doesn't exist
    pinecone.create_index("dagster-knowledge", dimension=1536)
    index, namespace_kwargs = pinecone.get_index("dagster-knowledge", namespace="dagster-github")

    # Get embeddings and upsert to Pinecone
    texts = [doc.page_content for doc in issue_docs]
    embeddings = pinecone.embed_texts(texts)

    # Prepare metadata
    metadatas = []
    for doc in issue_docs:
        meta = {}
        for k, v in doc.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                meta[k] = v
        metadatas.append(meta)

    # Upsert to Pinecone with namespace
    index.upsert(
        vectors=zip(
            [str(i) for i in range(len(texts))],  # IDs
            embeddings,
            metadatas,
        ),
        **namespace_kwargs,  # Include namespace parameters
    )

    return dg.MaterializeResult(
        metadata={
            "number_of_discussions": len(issues),
        }
    )


@dg.asset(
    group_name="ingestion",
    kinds={"github", "Pinecone", "openai"},
    partitions_def=daily_partition,
    automation_condition=dg.AutomationCondition.on_cron("@daily"),
)
def github_discussions(
    context: dg.AssetExecutionContext,
    github: GithubResource,
    pinecone: PineconeResource,
) -> dg.MaterializeResult:
    start, end = context.partition_time_window
    context.log.info(f"Finding issues from {start} to {end}")

    discussions = github.get_discussions(
        start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d")
    )

    discussion_docs = github.convert_discussions_to_documents(discussions)

    # Create index if doesn't exist
    pinecone.create_index("dagster-knowledge", dimension=1536)
    index, namespace_kwargs = pinecone.get_index("dagster-knowledge", namespace="dagster-github")

    # Get embeddings and upsert to Pinecone
    texts = [doc.page_content for doc in discussion_docs]
    embeddings = pinecone.embed_texts(texts)

    # Prepare metadata
    metadatas = []
    for doc in discussion_docs:
        meta = {}
        for k, v in doc.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                meta[k] = v
        metadatas.append(meta)

    # Upsert to Pinecone with namespace
    index.upsert(
        vectors=zip(
            [str(i) for i in range(len(texts))],  # IDs
            embeddings,
            metadatas,
        ),
        **namespace_kwargs,  # Include namespace parameters
    )

    return dg.MaterializeResult(
        metadata={
            "number_of_discussions": len(discussions),
        }
    )


doc_site_partition_def = dg.StaticPartitionsDefinition(
    partition_keys=scraper_resource.parse_sitemap()
)


# Webscraping asset
@dg.asset(
    partitions_def=doc_site_partition_def,
    group_name="ingestion",
    kinds={"webscraping", "Pinecone", "openai"},
    automation_condition=dg.AutomationCondition.on_cron(
        "0 0 * * 1"
    ),  # weekly on monday at midnight
)
def docs_scrape(
    context: dg.AssetExecutionContext, pinecone: PineconeResource, scraper: SitemapScraper
) -> dg.MaterializeResult:
    url = context.partition_key

    document = scraper.scrape_page(url)

    # Create index if doesn't exist
    pinecone.create_index("dagster-knowledge", dimension=1536)
    index, namespace_kwargs = pinecone.get_index("dagster-knowledge", namespace="dagster-docs")

    embedding = pinecone.embed_texts([document.page_content])[0]  # Single embedding
    meta = {k: v for k, v in document.metadata.items() if isinstance(v, (str, int, float, bool))}

    # Use namespace_kwargs in the upsert call
    doc_id = hashlib.md5(url.encode()).hexdigest()

    index.upsert(vectors=[(doc_id, embedding, meta)], **namespace_kwargs)

    return dg.MaterializeResult(
        metadata={"Page Scraped": url, "Page Title": document.metadata["title"]}
    )
