import json
import os

import dagster as dg
from langchain_core.documents import Document


# start_io_manager
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


# end_io_manager


@dg.io_manager(config_schema={"base_dir": str})
def document_io_manager(init_context):
    return DocumentIOManager(base_dir=init_context.resource_config["base_dir"])
