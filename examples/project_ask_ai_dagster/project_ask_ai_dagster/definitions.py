import dagster as dg
from project_ask_ai_dagster.resources.github import github_resource
from project_ask_ai_dagster.resources.openai import open_ai_resource
from project_ask_ai_dagster.resources.scraper import scraper_resource
from project_ask_ai_dagster.assets import ingestion

ingestion_assets = dg.load_assets_from_modules([ingestion])

defs = dg.Definitions(
    assets=ingestion_assets,
    resources={
        "github": github_resource,
        "open_ai": open_ai_resource,
        "scraper":scraper_resource,
    },
)