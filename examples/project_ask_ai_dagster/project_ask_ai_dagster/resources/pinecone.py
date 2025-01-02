import dagster as dg
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from pydantic import Field, PrivateAttr
from typing import Optional

class PineconeResource(dg.ConfigurableResource):
    pinecone_api_key: str = Field(description="Pinecone API key")
    openai_api_key: str = Field(description="OpenAI API key")
    pinecone_env: str = Field(description="Pinecone environment")
    _embeddings: OpenAIEmbeddings = PrivateAttr()

    def setup_for_execution(self, context: dg.InitResourceContext) -> None:
        self._pinecone = Pinecone(api_key=self.pinecone_api_key)
        self._embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", openai_api_key=self.openai_api_key
        )

    def create_index(self, index_name: str, dimension: int = 1536):
        if index_name not in self._pinecone.list_indexes().names():
            self._pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

    def get_index(self, index_name: str, namespace: str = Optional[T]):
        index = self._pinecone.Index(index_name)
        if namespace:
            return index, {"namespace": namespace}
        return index, {}

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)


pinecone_resource = PineconeResource(
    pinecone_api_key=dg.EnvVar("PINECONE_API_KEY"),
    openai_api_key=dg.EnvVar("OPENAI_API_KEY"),
    pinecone_env=dg.EnvVar("PINECONE_ENV"),
)
