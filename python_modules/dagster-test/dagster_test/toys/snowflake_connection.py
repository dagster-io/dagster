import random
from uuid import uuid4

import dagster as dg


@dg.observable_source_asset
def fake_snowflake_connection_asset(context: dg.OpExecutionContext):
    """Pretend this is a Snowflake connection asset."""
    return dg.ObserveResult(
        data_version=dg.DataVersion(str(uuid4())),
        metadata={
            "dagster/my_metric": dg.MetadataValue.int(random.randint(1, 100)),
        },
    )


def get_snowflake_connection_assets():
    return [fake_snowflake_connection_asset]
