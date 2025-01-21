import os

from dagster_chroma import ChromaResource, HttpConfig, LocalConfig

import dagster as dg


@dg.asset
def my_table(chroma: ChromaResource):
    with chroma.get_client() as chroma_client:
        collection = chroma_client.create_collection("fruits")

        collection.add(
            documents=[
                "This is a document about oranges",
                "This is a document about pineapples",
                "This is a document about strawberries",
                "This is a document about cucumbers",
            ],
            ids=["oranges", "pineapples", "strawberries", "cucumbers"],
        )

        results = collection.query(
            query_texts=["hawaii"],
            n_results=1,
        )


defs = dg.Definitions(
    assets=[my_table],
    resources={
        "chroma": ChromaResource(
            connection_config=LocalConfig(persistence_path="./chroma")
            if os.getenv("DEV")
            else HttpConfig(host="192.168.0.10", port=8000)
        ),
    },
)
