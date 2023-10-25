import pandas as pd

from dagster import MaterializeResult, MetadataValue, asset

# start_add_signsup_asset
from .resources import DataGeneratorResource

# ...


@asset
def signups(hackernews_api: DataGeneratorResource) -> MaterializeResult:
    signups = pd.DataFrame(hackernews_api.get_signups())

    signups.to_csv("data/signups.csv")

    return MaterializeResult(
        metadata={
            "Record Count": len(signups),
            "Preview": MetadataValue.md(signups.head().to_markdown()),
            "Earliest Signup": signups["registered_at"].min(),
            "Latest Signup": signups["registered_at"].max(),
        }
    )


# end_add_signsup_asset
