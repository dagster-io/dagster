import dagster as dg
import pandas as pd
import dagster_duckdb as dg_duckdb
from .resources import PineconeResource
from pinecone import ServerlessSpec

INDEX_NAME = "goodreads"
NAMESPACE = "ns1"


def _chunks(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


goodreads = dg.AssetSpec(
    "Goodreads",
    description="Goodreads Data. https://mengtingwan.github.io/data/goodreads#datasets",
    group_name="raw_data",
)


@dg.asset(
    kinds={"duckdb"},
    group_name="ingestion",
    deps=[goodreads],
)
def graphic_novels(duckdb_resource: dg_duckdb.DuckDBResource):
    url = "https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/goodreads/byGenre/goodreads_books_comics_graphic.json.gz"
    query = f"""
        create table if not exists graphic_novels as (
          select *
          from read_json(
            '{url}',
            ignore_errors = true
          )
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)


@dg.asset(
    kinds={"duckdb"},
    group_name="ingestion",
    deps=[goodreads],
)
def reviews(duckdb_resource: dg_duckdb.DuckDBResource):
    url = "https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/goodreads/byGenre/goodreads_reviews_comics_graphic.json.gz"
    query = f"""
        create table if not exists reviews as (
          select *
          from read_json(
            '{url}',
            ignore_errors = true
          )
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)


@dg.asset(
    kinds={"duckdb"},
    group_name="ingestion",
)
def enriched_reviews(
    duckdb_resource: dg_duckdb.DuckDBResource,
    graphic_novels,
    reviews,
) -> pd.DataFrame:
    query = f"""
        select
          reviews.review_id as review_id,
          graphic_novels.title as title,
          reviews.rating as rating,
          reviews.review_text as text
        from graphic_novels
        left join reviews
          on graphic_novels.book_id = reviews.book_id
        where graphic_novels.language_code = 'eng'
        limit 500
    """
    with duckdb_resource.get_connection() as conn:
        return conn.execute(query).fetch_df()


@dg.asset(
    kinds={"Pinecone"},
    group_name="processing",
)
def pinecone_index(
    pinecone_resource: PineconeResource,
):
    spec = ServerlessSpec(cloud="aws", region="us-east-1")
    pinecone_resource.create_index(
        INDEX_NAME,
        dimension=1024,
        metric="cosine",
        serverless_spec=spec,
    )


@dg.asset(
    kinds={"Pinecone"},
    group_name="processing",
)
def pinecone_embeddings(
    pinecone_resource: PineconeResource,
    enriched_reviews: pd.DataFrame,
    pinecone_index,
):
    data = enriched_reviews.to_dict("records")

    vectors = []
    for chunk in _chunks(data, 50):

        embeddings = pinecone_resource.embed(
            inputs=[r["text"] for r in chunk],
            input_type="passage",
        )

        for d, e in zip(chunk, embeddings):
            vectors.append(
                {
                    "id": str(d["review_id"]),
                    "values": e["values"],
                    "metadata": {
                        "source": "goodreads",
                        "rating": d["rating"],
                        "title": d["title"],
                        "text": d["text"],
                    },
                }
            )

    pinecone_resource.index(INDEX_NAME).upsert(
        vectors=vectors,
        namespace=NAMESPACE,
    )


class GoodreadsQuestion(dg.Config):
    question: str
    top_k: int


@dg.asset(
    kinds={"Pinecone"},
    group_name="retrieval",
)
def graphic_novel_search(
    context: dg.AssetExecutionContext,
    config: GoodreadsQuestion,
    pinecone_resource: PineconeResource,
    pinecone_embeddings,
):
    query_embedding = pinecone_resource.embed(
        inputs=[config.question],
        input_type="query",
    )
    index = pinecone_resource.index(INDEX_NAME)
    results = index.query(
        namespace=NAMESPACE,
        vector=query_embedding[0].values,
        top_k=config.top_k,
        include_values=False,
        include_metadata=True,
    )
    for result in results["matches"]:
        context.log.info(result)
