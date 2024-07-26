from dagster import Definitions, asset
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)


@asset(
    metadata={
        **CodeReferencesMetadataSet(
            code_references=CodeReferencesMetadataValue(
                code_references=[LocalFileCodeReference(file_path="foo.py", line_number=2)]
            )
        )
    }
)
def foo() -> int:
    return 1


defs = Definitions(assets=[foo])
