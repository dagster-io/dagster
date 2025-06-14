import dagster as dg
from dagster_openai import OpenAIResource

from project_ask_ai_dagster.defs.github import github_resource
from project_ask_ai_dagster.defs.io_managers import document_io_manager
from project_ask_ai_dagster.defs.pinecone import pinecone_resource
from project_ask_ai_dagster.defs.scraper import scraper_resource


# start_def
@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "github": github_resource,
            "scraper": scraper_resource,
            "pinecone": pinecone_resource,
            "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
            "document_io_manager": document_io_manager.configured(
                {"base_dir": "data/documents"},
            ),
        },
    )


# end_def
