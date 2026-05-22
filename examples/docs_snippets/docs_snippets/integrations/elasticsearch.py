from dagster_elasticsearch import (
    ElasticsearchIOManager,
    ElasticsearchResource,
    HostsConfig,
    build_indexed_asset_check,
)

import dagster as dg


@dg.asset(compute_kind="elasticsearch")
def indexed_doc(es: ElasticsearchResource) -> None:
    with es.get_client() as client:
        client.index(index="docs", id="hello", document={"title": "hello"})
        client.indices.refresh(index="docs")


@dg.asset(io_manager_key="elasticsearch_io_manager")
def search_docs() -> list[dict[str, str]]:
    return [
        {"_id": "1", "title": "hello"},
        {"_id": "2", "title": "world"},
    ]


defs = dg.Definitions(
    assets=[indexed_doc, search_docs],
    asset_checks=[build_indexed_asset_check(asset=search_docs, min_indexed=1)],
    resources={
        "es": ElasticsearchResource(
            connection_config=HostsConfig(
                hosts=["https://es.example.com:9200"],
                api_key=dg.EnvVar("ELASTICSEARCH_API_KEY"),
            ),
        ),
        "elasticsearch_io_manager": ElasticsearchIOManager(
            connection_config=HostsConfig(
                hosts=["https://es.example.com:9200"],
                api_key=dg.EnvVar("ELASTICSEARCH_API_KEY"),
            ),
            index="docs",
            use_alias=True,
            rollover_strategy="auto",
            keep_last=3,
        ),
    },
)
