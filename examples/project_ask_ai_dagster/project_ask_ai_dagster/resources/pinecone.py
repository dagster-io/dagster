from typing import Optional

import dagster as dg
from pinecone import Pinecone
from pydantic import Field


class PineconeResource(dg.ConfigurableResource):
    pinecone_api_key: str = Field(description="Pinecone API key")
    openai_api_key: str = Field(description="OpenAI API key")

    def setup_for_execution(self, context: dg.InitResourceContext) -> None:
        self._pinecone = Pinecone(api_key=self.pinecone_api_key)  # type: ignore

    def create_index(self, index_name: str, dimension: int = 1536):
        if index_name not in self._pinecone.list_indexes().names():
            self._pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
            )

    def get_index(self, index_name: str, namespace: Optional[str] = None):
        index = self._pinecone.Index(index_name)
        if namespace:
            return index, {"namespace": namespace}
        return index, {}


pinecone_resource = PineconeResource(
    pinecone_api_key=dg.EnvVar("PINECONE_API_KEY"), openai_api_key=dg.EnvVar("OPENAI_API_KEY")
)
