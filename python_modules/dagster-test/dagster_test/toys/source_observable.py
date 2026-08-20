import random
from uuid import uuid4

import dagster as dg


@dg.observable_source_asset
def source_observable_asset_with_metadata(context: dg.OpExecutionContext):
    """A source observable asset that emits metadata in observations."""
    return dg.ObserveResult(
        data_version=dg.DataVersion(str(uuid4())),
        metadata={
            "dagster/row_count": dg.MetadataValue.int(random.randint(1, 100)),
        },
    )


def get_source_observable_assets():
    return [source_observable_asset_with_metadata]
