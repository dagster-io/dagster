import pandas as pd

from dagster import AssetExecutionContext, MetadataValue, asset

# start_add_signsup_asset
from ..resources import DataGeneratorResource

# ...


@asset
def signups(
    context: AssetExecutionContext, hackernews_api: DataGeneratorResource
) -> pd.DataFrame:
    signups = pd.DataFrame(hackernews_api.get_signups())

    context.add_output_metadata(
        metadata={
            "Record Count": len(signups),
            "Preview": MetadataValue.md(signups.head().to_markdown()),
            "Earliest Signup": signups["registered_at"].min(),
            "Latest Signup": signups["registered_at"].max(),
        }
    )

    return signups


# end_add_signsup_asset
