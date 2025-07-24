from dagster import Enum, EnumValue
from dagster._annotations import public

SparkDeployModeCluster = EnumValue("cluster")
SparkDeployModeClient = EnumValue("client")
SparkDeployMode = Enum(
    name="SparkDeployMode", enum_values=[SparkDeployModeCluster, SparkDeployModeClient]
)


@public
class SparkOpError(Exception):
    pass
