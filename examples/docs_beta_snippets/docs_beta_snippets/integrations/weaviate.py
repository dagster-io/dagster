from dagster_weaviate import CloudConfig, WeaviateResource

import dagster as dg


@dg.asset
def my_table(weaviate: WeaviateResource):
    with weaviate.get_client() as weaviate_client:
        questions = weaviate_client.collections.get("Question")
        questions.query.near_text(query="biology", limit=2)


defs = dg.Definitions(
    assets=[my_table],
    resources={
        "weaviate": WeaviateResource(
            connection_config=CloudConfig(cluster_url=dg.EnvVar("WCD_URL")),
            auth_credentials={"api_key": dg.EnvVar("WCD_API_KEY")},
            headers={
                "X-Cohere-Api-Key": dg.EnvVar("COHERE_API_KEY"),
            },
        ),
    },
)
