import dagster as dg
from . import assets

goodreads_pinecone = dg.define_asset_job(
    name="goodreads_pinecone",
    selection=[
        assets.graphic_novels,
        assets.reviews,
        assets.enriched_reviews,
        assets.pinecone_index,
        assets.pinecone_embeddings,
    ],
)
