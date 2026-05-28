from dagster_hf_datasets._export import HFDatasetPublisher
from dagster_hf_datasets.assets import hf_dataset_asset
from dagster_hf_datasets.io_manager import HFParquetIOManager
from dagster_hf_datasets.resources import HuggingFaceResource
from datasets import Dataset

from dagster import AssetExecutionContext, Definitions, asset


@hf_dataset_asset(
    path="nyu-mll/glue",  # Authenticate first with: hf auth login
    config="qqp",
    split="train",
    group_name="golden_glue_pipeline",
    io_manager_key="hf_parquet_io_manager",
)
def raw_glue_qqp():
    """Load the raw GLUE QQP training split
    from the Hugging Face Hub.
    """
    pass


@asset(
    io_manager_key="hf_parquet_io_manager",
    group_name="golden_glue_pipeline",
)
def deduplicated_glue_qqp(
    raw_glue_qqp: Dataset,
) -> Dataset:
    """Remove duplicate question pairs."""
    seen = set()

    def unique_example(example: dict) -> bool:
        key = (
            example["question1"],
            example["question2"],
        )

        if key in seen:
            return False

        seen.add(key)
        return True

    return raw_glue_qqp.filter(unique_example)


@asset(
    io_manager_key="hf_parquet_io_manager",
    group_name="golden_glue_pipeline",
)
def filtered_glue_qqp(
    deduplicated_glue_qqp: Dataset,
) -> Dataset:
    """Remove malformed and short examples."""

    def valid_example(example: dict) -> bool:
        q1 = example["question1"]
        q2 = example["question2"]

        return (
            q1 is not None
            and q2 is not None
            and len(q1.split()) >= 5
            and len(q2.split()) >= 5
        )

    return deduplicated_glue_qqp.filter(valid_example)


@asset(
    io_manager_key="hf_parquet_io_manager",
    group_name="golden_glue_pipeline",
)
def golden_glue_qqp(
    filtered_glue_qqp: Dataset,
) -> Dataset:
    """Normalize text formatting and
    produce a curated "golden" dataset.
    """

    def normalize(example: dict) -> dict:
        return {
            "question1": (example["question1"].strip().lower()),
            "question2": (example["question2"].strip().lower()),
            "label": example["label"],
        }

    return filtered_glue_qqp.map(normalize)


@asset(
    io_manager_key="hf_parquet_io_manager",
    group_name="golden_glue_pipeline",
)
def publish_golden_glue(
    context: AssetExecutionContext,
    golden_glue_qqp: Dataset,
) -> str:
    """Publish the processed dataset
    to the Hugging Face Hub.
    """
    context.log.info("Preparing dataset publication")

    context.log.info(
        "Dataset rows: %s",
        len(golden_glue_qqp),
    )

    publisher = HFDatasetPublisher(
        repo_id="username/golden-glue-qqp",
        private=False,
    )

    hub_url = publisher.publish(
        dataset=golden_glue_qqp,
        source_dataset="nyu-mll/glue",
        source_revision="main",
        description=(
            "Curated GLUE QQP dataset "
            "with deduplication, filtering, "
            "and normalization applied."
        ),
        processing_steps=[
            "Removed duplicate question pairs",
            "Removed malformed examples",
            "Filtered short questions",
            "Normalized text formatting",
        ],
        metadata={
            "task": ("duplicate-question-detection"),
            "source_config": "qqp",
            "pipeline": ("golden_dataset_pipeline"),
        },
    )

    context.log.info("Dataset successfully pushed to the Hugging Face Hub")

    context.log.info(
        "Hub URL: %s",
        hub_url,
    )

    return hub_url


defs = Definitions(
    assets=[
        raw_glue_qqp,
        deduplicated_glue_qqp,
        filtered_glue_qqp,
        golden_glue_qqp,
        publish_golden_glue,
    ],
    resources={
        "huggingface": HuggingFaceResource(
            cache_dir=".hf_cache",
            offline=False,
        ),
        "hf_parquet_io_manager": (
            HFParquetIOManager(
                base_dir=".dagster_hf_storage",
            )
        ),
    },
)
