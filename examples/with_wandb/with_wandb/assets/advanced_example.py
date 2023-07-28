import wandb
from dagster import AssetExecutionContext, AssetIn, asset
from dagster_wandb import WandbArtifactConfiguration
from wandb import Artifact

wandb_artifact_configuration: WandbArtifactConfiguration = {
    "description": "My **Markdown** description",
    "aliases": ["first_alias", "second_alias"],
    "add_dirs": [
        {
            "name": "My model directory",
            "local_path": "with_wandb/assets/example",
        }
    ],
    "add_files": [
        {
            "name": "my_training_script",
            "local_path": "with_wandb/assets/example/train.py",
        },
        {
            "is_tmp": True,
            "local_path": "with_wandb/assets/example/README.md",
        },
    ],
}

MY_ASSET = "my_advanced_artifact"
MY_TABLE = "my_table"


@asset(
    name=MY_ASSET,
    compute_kind="wandb",
    metadata={"wandb_artifact_configuration": wandb_artifact_configuration},
)
def write_advanced_artifact() -> Artifact:
    """Example that writes an advanced Artifact.

    Here we use the full power of the integration with W&B Artifacts.

    We create a custom Artifact that contains a W&B Table. You could also return the Table directly
    but for advanced scenario you will want to create an Artifact directly.

    We use the integration to augment that Artifact. This includes:
    - Adding a Markdown description
    - Tagging the Artifact with two aliases
    - We are also attaching a folder and a file. That part is a purposely contrived to
    show the capabilities of the integration.

    This is all done through the metadata on the asset.

    The properties you can pass to 'add_dirs', 'add_files', 'add_references' are the same as the
    homonymous method's in the SDK.

    Reference:
    - https://docs.wandb.ai/ref/python/artifact#add_dir
    - https://docs.wandb.ai/ref/python/artifact#add_file
    - https://docs.wandb.ai/ref/python/artifact#add_reference

    Returns:
        Artifact: The Artifact we augment with the integration
    """
    artifact = wandb.Artifact(MY_ASSET, "files")
    table = wandb.Table(columns=["a", "b", "c"], data=[[1, 2, 3]])
    artifact.add(table, MY_TABLE)
    return artifact


@asset(
    compute_kind="wandb",
    ins={
        "table": AssetIn(
            key=MY_ASSET,
            metadata={
                "wandb_artifact_configuration": {
                    "get": MY_TABLE,
                }
            },
        )
    },
    output_required=False,
)
def get_table(context: AssetExecutionContext, table: wandb.Table) -> None:
    """Example that reads a W&B Table contained in an Artifact.

    Args:
        context (AssetExecutionContext): Dagster execution context
        table (wandb.Table): Table contained in our downloaded Artifact

    Here, we use the integration to read the W&B Table object created in the previous asset.

    The integration downloads the Artifact for us. We can simply annotate our asset and use the
    the W&B Table object directly.
    """
    context.log.info(f"Result: {table.get_column('a')}")  # Result: [1]


@asset(
    compute_kind="wandb",
    ins={
        "path": AssetIn(
            key=MY_ASSET,
            metadata={
                "wandb_artifact_configuration": {
                    "get_path": "my_training_script",
                }
            },
        )
    },
    output_required=False,
)
def get_path(context: AssetExecutionContext, path: str) -> None:
    """Example that gets the local path of a file contained in an Artifact.

    Args:
        context (AssetExecutionContext): Dagster execution context
        path (str): Path in the local filesystem of the downloaded file

    Here, we use the integration to collect the local of the file added through the 'add_dirs' in
    the metadata of the first asset.

    The integration downloads the file for us. We can use that file as any other file.
    """
    context.log.info(f"Result: {path}")


@asset(
    compute_kind="wandb",
    ins={
        "artifact": AssetIn(
            key=MY_ASSET,
        )
    },
    output_required=False,
)
def get_artifact(context: AssetExecutionContext, artifact: Artifact) -> None:
    """Example that gets the entire Artifact object.

    Args:
        context (AssetExecutionContext): Dagster execution context
        artifact (Artifact): Downloaded Artifact object

    Here, we use the integration to collect the entire W&B Artifact object created from in first
    asset.

    The integration downloads the entire Artifact for us.
    """
    context.log.info(f"Result: {artifact.name}")  # Result: my_advanced_artifact:v0


@asset(
    compute_kind="wandb",
    ins={
        "artifact": AssetIn(
            key=MY_ASSET,
            metadata={
                "wandb_artifact_configuration": {
                    "version": "v0",
                }
            },
        )
    },
    output_required=False,
)
def get_version(context: AssetExecutionContext, artifact: Artifact) -> None:
    """Example that gets the entire Artifact object based on its version.

    Args:
        context (AssetExecutionContext): Dagster execution context
        artifact (Artifact): Downloaded Artifact object
    """
    context.log.info(f"Result: {artifact.name}")  # Result: my_advanced_artifact:v0


@asset(
    compute_kind="wandb",
    ins={
        "artifact": AssetIn(
            key=MY_ASSET,
            metadata={
                "wandb_artifact_configuration": {
                    "alias": "first_alias",
                }
            },
        )
    },
    output_required=False,
)
def get_alias(context: AssetExecutionContext, artifact: Artifact) -> None:
    """Example that gets the entire Artifact object based on its alias.

    Args:
        context (AssetExecutionContext): Dagster execution context
        artifact (Artifact): Downloaded Artifact object
    """
    context.log.info(f"Result: {artifact.name}")  # Result: my_advanced_artifact:first_alias
