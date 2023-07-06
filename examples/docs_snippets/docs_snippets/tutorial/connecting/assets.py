import pandas as pd

from dagster import MetadataValue, Output, asset

# start_add_signsup_asset
from .resources.data_generator import DataGeneratorResource

# ...


@asset
def signups(hackernews_api: DataGeneratorResource):
    signups = pd.DataFrame(hackernews_api.get_signups())

    return Output(
        value=signups,
        metadata={
            "Record Count": len(signups),
            "Preview": MetadataValue.md(signups.head().to_markdown()),
            "Earliest Signup": signups["registered_at"].min(),
            "Latest Signup": signups["registered_at"].max(),
        },
    )


# end_add_signsup_asset
