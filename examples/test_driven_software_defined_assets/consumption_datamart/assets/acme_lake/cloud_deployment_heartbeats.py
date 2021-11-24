import warnings
from textwrap import dedent

import pandas

import dagster
from dagster import Output, EventMetadata
from dagster.core.asset_defs import asset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


@asset(
    namespace='acme_lake',
    compute_kind='lake',
    required_resource_keys={"datawarehouse"},
)
def cloud_deployment_heartbeats(context) -> pandas.DataFrame:
    """An immutable snapshot of heartbeat telemetry received from ACME's Cloud service offering"""

    df = context.resources.datawarehouse.read_sql_query('''
        SELECT
            ts
        ,   customer_id
        ,   deployment_id
        ,   infrastructure
        ,   vcpu_usage
        ,   memory_usage
        FROM acme_lake.cloud_deployment_heartbeats
    ''')

    yield Output(
        df,
        metadata={
            "Data Dictionary": EventMetadata.md(dedent(f"""
                | Column              	         | Type   	 | Description                                                                       |
                |--------------------------------|-----------|-----------------------------------------------------------------------------------|
                | ts                	         | Timestamp | Timestamp when the heartbeat data was received                                    |
                | customer_id          	         | String 	 | Customer Identifier                                                               |
                | deployment_id   	             | String 	 | Deployment Identifier                                                             |
                | infrastructure             	 | String 	 | Infrastructure the deployment is running on - eg: AWS_EC2, AZURE_COMPUTE, GCP_GCE |
                | vcpu_usage                     | Decimal 	 | Quantity of VCPU usage used by this deployment at time: ts                        |
                | memory_usage                   | Decimal	 | Quantity of Memory used (in GB) by this deployment at time: ts                    |                
            """)),
            "n_rows": EventMetadata.int(len(df)),
            "tail(5)": EventMetadata.md(df.tail(5).to_markdown()),
        },
    )
