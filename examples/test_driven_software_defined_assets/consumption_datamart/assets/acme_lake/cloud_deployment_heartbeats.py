import warnings

from sqlalchemy import Column, String, Numeric, DateTime

import dagster
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output
from dagster.core.asset_defs import asset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


class CloudDeploymentHeartbeatsDataFrameSchema:
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


CloudDeploymentHeartbeatsDataFrameType = make_typed_dataframe_dagster_type(
    "CloudDeploymentHeartbeatsDataFrame", CloudDeploymentHeartbeatsDataFrameSchema)

@asset(
    namespace='acme_lake',
    compute_kind='lake',
    required_resource_keys={"datawarehouse"},
)
def cloud_deployment_heartbeats(context) -> CloudDeploymentHeartbeatsDataFrameType:
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

    typed_df = CloudDeploymentHeartbeatsDataFrameType.convert_dtypes(df)

    return Output(typed_df, metadata=CloudDeploymentHeartbeatsDataFrameType.extract_event_metadata(df))
