import warnings

from sqlalchemy import Column, String, Numeric, DateTime

import dagster
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import AssetKey, Output, DagsterTypeLoader, dagster_type_loader, AssetMaterialization
from dagster.core.asset_defs import ForeignAsset, asset

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


@dagster_type_loader(
    required_resource_keys={"datawarehouse"},
    config_schema={}
)
def cloud_deployment_heartbeats_loader(context, _config):
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

    df['meta__warnings'] = ''

    typed_df = CloudDeploymentHeartbeatsDataFrameType.convert_dtypes(df)

    # TODO: Figure out where to emit this metadata - yielding as AssetMaterialization like this causes a
    # dagster.core.errors.DagsterTypeCheckDidNotPass: Type check failed for step input "cloud_deployment_heartbeats" -
    # expected type "CloudDeploymentHeartbeatsDataFrame". Description: Must be a pandas.DataFrame. Got value of type. generator
    # yield AssetMaterialization(
    #     asset_key=context.asset_key,
    #     metadata=context.dagster_type.extract_event_metadata(typed_df),
    # )

    return typed_df


CloudDeploymentHeartbeatsDataFrameType = make_typed_dataframe_dagster_type(
    "CloudDeploymentHeartbeatsDataFrame",
    schema=CloudDeploymentHeartbeatsDataFrameSchema,
    dataframe_loader=cloud_deployment_heartbeats_loader
)

cloud_deployment_heartbeats = ForeignAsset(
    key=AssetKey(["acme_lake", "cloud_deployment_heartbeats"]),
    io_manager_key="lake_input_manager",
)
