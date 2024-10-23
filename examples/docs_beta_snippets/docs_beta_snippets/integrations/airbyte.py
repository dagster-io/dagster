from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance

import dagster as dg

# Load all assets from your Airbyte instance
airbyte_assets = load_assets_from_airbyte_instance(
    # Connect to your OSS Airbyte instance
    AirbyteResource(
        host="localhost",
        port="8000",
        # If using basic auth, include username and password:
        username="airbyte",
        password=dg.EnvVar("AIRBYTE_PASSWORD"),
    )
)

defs = dg.Definitions(
    assets=[airbyte_assets],
)
