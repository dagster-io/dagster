from dagster_hf_datasets._metadata import build_dataset_metadata
from dagster_hf_datasets.assets import hf_dataset_asset
from dagster_hf_datasets.io_manager import HFParquetIOManager
from dagster_hf_datasets.resources import HuggingFaceResource

from dagster import AssetExecutionContext, Definitions, MaterializeResult

resources = {
    "huggingface": HuggingFaceResource(
        cache_dir=".hf_cache",
        offline=False,
    ),
    "hf_parquet_io_manager": (
        HFParquetIOManager(
            base_dir=".dagster_hf_storage",
        )
    ),
}


@hf_dataset_asset(
    path="nyu-mll/glue",  # Authenticate first with: hf auth login
    config="qqp",
    split="train",
    group_name="huggingface_datasets",
    io_manager_key="hf_parquet_io_manager",
)
def glue_qqp_train(
    context: AssetExecutionContext,
    dataset,
):
    """Materialize the GLUE QQP training split
    as a Dagster asset backed by a
    Hugging Face Dataset.

    Demonstrates:
    - dataset materialization
    - parquet persistence
    - metadata enrichment
    - Hugging Face Hub observability
    """
    metadata = build_dataset_metadata(
        dataset,
        path="nyu-mll/glue",
    )

    context.log.info(
        "Loaded dataset with %s rows",
        len(dataset),
    )

    for key, value in metadata.items():
        context.log.info(
            "%s: %s",
            key,
            value,
        )

    return MaterializeResult(
        value=dataset,
        metadata=metadata,
    )


defs = Definitions(
    assets=[
        glue_qqp_train,
    ],
    resources=resources,
)
