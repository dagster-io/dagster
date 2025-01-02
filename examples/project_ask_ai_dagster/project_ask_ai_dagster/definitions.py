import dagster as dg

from project_ask_ai_dagster.assets import ingestion
from project_ask_ai_dagster.resources.github import github_resource
from project_ask_ai_dagster.resources.pinecone import pinecone_resource
from project_ask_ai_dagster.resources.scraper import scraper_resource

ingestion_assets = dg.load_assets_from_modules([ingestion])

defs = dg.Definitions(
    assets=ingestion_assets,
    resources={
        "github": github_resource,
        "scraper": scraper_resource,
        "pinecone": pinecone_resource,
    },
)
