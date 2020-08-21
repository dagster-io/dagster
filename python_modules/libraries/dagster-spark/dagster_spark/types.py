from dagster import Enum, EnumValue

SparkDeployModeCluster = EnumValue("cluster")
SparkDeployModeClient = EnumValue("client")
SparkDeployMode = Enum(
    name="SparkDeployMode", enum_values=[SparkDeployModeCluster, SparkDeployModeClient]
)


class SparkSolidError(Exception):
    pass
