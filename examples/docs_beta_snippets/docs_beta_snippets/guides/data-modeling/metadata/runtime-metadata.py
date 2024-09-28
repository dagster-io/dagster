import dagster as dg


@dg.asset
def my_asset():
    # Asset logic goes here
    return dg.MaterializeResult(
        metadata={
            # file_size_kb will be rendered as a time series
            "file_size_kb": dg.MetadataValue.int(...)
        }
    )
