import warnings

from sqlalchemy import Column, String, Numeric, DateTime

import dagster
from consumption_datamart.assets.typed_dataframe.dataframe_schema import DataFrameSchema
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type, list_to_str, str_to_list
from dagster import AssetKey
from dagster.core.asset_defs import ForeignAsset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


class CloudDeploymentHeartbeatsDataFrameSchema(DataFrameSchema):
    order_date = Column(
        'ts', DateTime, nullable=False,
        comment="Timestamp when the heartbeat data was received  ")
    customer_id = Column(
        'customer_id', String, nullable=False,
        comment="Customer Identifier")
    deployment_id = Column(
        'deployment_id', String, nullable=False,
        comment="Deployment Identifier")
    infrastructure = Column(
        'infrastructure', String, nullable=False,
        comment="Infrastructure the deployment is running on - eg: AWS_EC2, AZURE_COMPUTE, GCP_GCE")
    vcpu_usage = Column(
        'vcpu_usage', Numeric(12, 2), nullable=False,
        comment="Quantity of VCPU usage used by this deployment at time: ts ")
    memory_usage = Column(
        'memory_usage', Numeric(12, 2), nullable=False,
        comment="Quantity of Memory used (in GB) by this deployment at time: ts")

    @staticmethod
    def calculate_data_quality(df):
        df['meta__warnings'] = df['meta__warnings'].apply(str_to_list)

        has_invalid_customer_id = ~df.customer_id.str.match(r'^CUST-\d+$')
        df.loc[has_invalid_customer_id, 'meta__warnings'] = df.loc[has_invalid_customer_id, 'meta__warnings'].apply(lambda w: w + ['invalid_customer_id'])

        df.loc[:, 'meta__warnings'] = df['meta__warnings'].apply(list_to_str)

        return df


CloudDeploymentHeartbeatsDataFrameType = make_typed_dataframe_dagster_type(
    "CloudDeploymentHeartbeatsDataFrame",
    schema=CloudDeploymentHeartbeatsDataFrameSchema()
)

cloud_deployment_heartbeats = ForeignAsset(
    key=AssetKey(["acme_lake", "cloud_deployment_heartbeats"]),
    description="An immutable snapshot containing all cloud deployment heartbeat data",
    io_manager_key="datawarehouse_io_manager",
    metadata={
        "load_sql": """
        SELECT
            ts
        ,   customer_id
        ,   deployment_id
        ,   infrastructure
        ,   vcpu_usage
        ,   memory_usage
        FROM acme_lake.cloud_deployment_heartbeats
        """,
        "dagster_type": CloudDeploymentHeartbeatsDataFrameType
    }
)
