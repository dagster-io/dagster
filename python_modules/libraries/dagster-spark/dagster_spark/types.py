'''Type definitions for the event pipeline demo'''

from dagster import DagsterUserError, Enum, EnumValue


SparkDeployModeCluster = EnumValue('cluster')
SparkDeployModeClient = EnumValue('client')
SparkDeployMode = Enum(
    name='SparkDeployMode', enum_values=[SparkDeployModeCluster, SparkDeployModeClient]
)


class SparkSolidError(DagsterUserError):
    pass


SparkSolidOutputModeSuccess = EnumValue('output_success')
SparkSolidOutputModePaths = EnumValue('paths')
SparkSolidOutputMode = Enum(
    name='SparkOutputMode', enum_values=[SparkSolidOutputModeSuccess, SparkSolidOutputModePaths]
)
