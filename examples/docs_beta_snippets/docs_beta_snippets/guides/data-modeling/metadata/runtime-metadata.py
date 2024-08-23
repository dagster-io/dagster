from dagster import MaterializeResult, MetadataValue, asset


@asset
def my_asset():
    # Asset logic goes here
    return MaterializeResult(
        metadata={
            # file_size_kb will be rendered as a time series
            "file_size_kb": MetadataValue.int(...)
        }
    )
