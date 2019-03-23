"""Type definitions for the airline_demo."""

from dagster.core.types.config import ConfigEnum, EnumValue


SparkDeployModeCluster = EnumValue('cluster')
SparkDeployModeClient = EnumValue('client')
SparkDeployMode = ConfigEnum(
    name='SparkDeployMode', enum_values=[SparkDeployModeCluster, SparkDeployModeClient]
)

SparkDeployTargetLocal = EnumValue('Spark Deploy Target: Local')
SparkDeployTargetRemote = EnumValue('Spark Deploy Target: Remote')
SparkDeployTargetAWSEMR = EnumValue('Spark Deploy Target: AWS EMR')
SparkDeployTargetGCPDataproc = EnumValue('Spark Deploy Target: GCP Dataproc')
SparkDeployTarget = ConfigEnum(
    name='SparkDeployTarget',
    enum_values=[
        SparkDeployTargetLocal,
        SparkDeployTargetRemote,
        SparkDeployTargetAWSEMR,
        SparkDeployTargetGCPDataproc,
    ],
)

