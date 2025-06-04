import dagster as dg
from dagster_openai import OpenAIResource

import project_ask_ai_dagster.defs
from project_ask_ai_dagster.defs.io_managers import document_io_manager
from project_ask_ai_dagster.defs.resources.github import github_resource
from project_ask_ai_dagster.defs.resources.pinecone import pinecone_resource
from project_ask_ai_dagster.defs.resources.scraper import scraper_resource

# start_def
defs = dg.Definitions.merge(
    dg.components.load_defs(project_ask_ai_dagster.defs),
    dg.Definitions(
        resources={
            "github": github_resource,
            "scraper": scraper_resource,
            "pinecone": pinecone_resource,
            "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
            # IO Manager
            "document_io_manager": document_io_manager.configured(
                {"base_dir": "data/documents"},
            ),
        },
    ),
)


# end_def
