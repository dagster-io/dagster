import os

from dagster import Definitions, asset
from dagster._core.definitions.metadata import (
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
    with_source_code_references,
)


@asset(
    metadata={
        "dagster/code_references": CodeReferencesMetadataValue(
            code_references=[
                LocalFileCodeReference(
                    file_path=os.path.join(os.path.dirname(__file__), "source.yaml"),
                    # Label and line number are optional
                    line_number=1,
                    label="Model YAML",
                )
            ]
        )
    }
)
def my_asset_modeled_in_yaml(): ...


defs = Definitions(assets=with_source_code_references([my_asset_modeled_in_yaml]))
