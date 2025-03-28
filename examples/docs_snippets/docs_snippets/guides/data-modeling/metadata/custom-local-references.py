import dagster as dg


@dg.asset(
    metadata={
        "dagster/code_references": dg.CodeReferencesMetadataValue(
            code_references=[
                dg.LocalFileCodeReference(
                    file_path="/path/to/source.yaml",
                    # Label and line number are optional
                    line_number=1,
                    label="Model YAML",
                )
            ]
        )
    }
)
def my_asset_modeled_in_yaml(): ...


defs = dg.Definitions(assets=dg.with_source_code_references([my_asset_modeled_in_yaml]))
