from dagster_pipes.transforms.transform import (
    transform,
    TransformResult,
    Upstream,
    execute_asset_key,
)
from dagster_pipes import open_dagster_pipes
from typing import Annotated
from dagster_transforms_1.lib.file_storage_io import FileStorageIO


@transform(assets=["one"])
def return_one(context) -> TransformResult:
    return TransformResult.asset("one", 1)


@transform(assets=["two"])
def add_one(context, up: Annotated[int, Upstream(return_one)]) -> TransformResult:
    return TransformResult.asset("two", up + 1)


if __name__ == "__main__":
    with open_dagster_pipes() as context:
        storage_result = execute_asset_key(
            asset_key=context.asset_key,
            storage_io=FileStorageIO("/tmp/dagster-transforms-1"),
            transforms=[return_one, add_one],
        )
        for asset_key, value in storage_result.assets.items():
            context.report_asset_materialization(
                asset_key=asset_key, metadata={"value": str(value)}
            )
