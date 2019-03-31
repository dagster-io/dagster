'''Type definitions for the event pipeline demo'''

from dagster import DagsterUserCodeExecutionError, Enum, EnumValue


SparkDeployModeCluster = EnumValue('cluster')
SparkDeployModeClient = EnumValue('client')
SparkDeployMode = Enum(
    name='SparkDeployMode', enum_values=[SparkDeployModeCluster, SparkDeployModeClient]
)


class SparkSolidError(DagsterUserCodeExecutionError):
    pass
