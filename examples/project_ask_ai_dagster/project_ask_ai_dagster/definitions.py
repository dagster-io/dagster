import json
import os

import dagster as dg
from dagster_openai import OpenAIResource
from langchain_core.documents import Document

from project_ask_ai_dagster.assets import ingestion, retrieval
from project_ask_ai_dagster.resources.github import github_resource
from project_ask_ai_dagster.resources.pinecone import pinecone_resource
from project_ask_ai_dagster.resources.scraper import scraper_resource


class DocumentIOManager(dg.IOManager):
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def handle_output(self, context, obj):
        # Convert documents to simple dicts
        file_path = os.path.join(self.base_dir, f"{context.asset_key.path[-1]}.json")

        # Convert documents to simple dicts
        serialized_docs = [
            {"page_content": doc.page_content, "metadata": doc.metadata} for doc in obj
        ]

        # Save as JSON
        with open(file_path, "w") as f:
            json.dump(serialized_docs, f)

    def load_input(self, context):
        file_path = os.path.join(self.base_dir, f"{context.asset_key.path[-1]}.json")

        if not os.path.exists(file_path):
            return []

        # Load and reconstruct Documents
        with open(file_path) as f:
            data = json.load(f)

        return [
            Document(page_content=doc["page_content"], metadata=doc["metadata"]) for doc in data
        ]


@dg.io_manager(config_schema={"base_dir": str})
def document_io_manager(init_context):
    return DocumentIOManager(base_dir=init_context.resource_config["base_dir"])


ingestion_assets = dg.load_assets_from_modules([ingestion])
retrieval_assets = dg.load_assets_from_modules([retrieval])


defs = dg.Definitions(
    assets=[*ingestion_assets, *retrieval_assets],
    resources={
        "github": github_resource,
        "scraper": scraper_resource,
        "pinecone": pinecone_resource,
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
        "document_io_manager": document_io_manager.configured({"base_dir": "data/documents"}),
    },
)
