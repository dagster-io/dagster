from dagster_qdrant import QdrantConfig, QdrantResource

import dagster as dg


@dg.asset
def my_table(qdrant_resource: QdrantResource):
    with qdrant_resource.get_client() as qdrant:
        qdrant.add(
            collection_name="test_collection",
            documents=[
                "This is a document about oranges",
                "This is a document about pineapples",
                "This is a document about strawberries",
                "This is a document about cucumbers",
            ],
        )
        results = qdrant.query(
            collection_name="test_collection", query_text="hawaii", limit=3
        )


defs = dg.Definitions(
    assets=[my_table],
    resources={
        "qdrant_resource": QdrantResource(
            config=QdrantConfig(
                host="xyz-example.eu-central.aws.cloud.qdrant.io",
                api_key="<your-api-key>",
            )
        )
    },
)
