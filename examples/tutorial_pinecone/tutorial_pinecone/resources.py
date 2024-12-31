import dagster as dg
from pinecone import Pinecone, ServerlessSpec
from pinecone.core.openapi.control.model.embeddings_list import EmbeddingsList
from pydantic import Field, PrivateAttr
import dagster_duckdb as dg_duckdb
import time


class PineconeResource(dg.ConfigurableResource):
    api_key: str = Field(
        description=(
            "Pinecone API key. See https://docs.pinecone.io/reference/api/introduction"
        )
    )

    _client: Pinecone = PrivateAttr()

    def setup_for_execution(self, context: dg.InitResourceContext) -> None:
        self._client = Pinecone(
            api_key=self.api_key,
        )

    def create_index(
        self,
        index_name: str,
        dimension: int,
        metric: str,
        serverless_spec: ServerlessSpec,
    ):
        existing_indexes = [
            index_info["name"] for index_info in self._client.list_indexes()
        ]

        if index_name not in existing_indexes:
            self._client.create_index(
                index_name,
                dimension=dimension,
                metric=metric,
                spec=serverless_spec,
            )
            while not self._client.describe_index(index_name).status["ready"]:
                time.sleep(1)

    def index(self, index_name: str) -> Pinecone.Index:
        return self._client.Index(index_name)

    def embed(
        self,
        inputs: list[str],
        input_type: str,
    ) -> EmbeddingsList:
        return self._client.inference.embed(
            model="multilingual-e5-large",
            inputs=inputs,
            parameters={"input_type": input_type},
        )


duckdb_resouce = dg_duckdb.DuckDBResource(database="data/data.duckdb")
pinecone_resource = PineconeResource(api_key=dg.EnvVar("PINECONE_API_KEY"))
