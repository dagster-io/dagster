import re

from dagster import Enum, EnumValue
from dagster._config.errors import PostProcessingError
from dagster._config.source import StringSourceType

SparkDeployModeCluster = EnumValue("cluster")
SparkDeployModeClient = EnumValue("client")
SparkDeployMode = Enum(
    name="SparkDeployMode", enum_values=[SparkDeployModeCluster, SparkDeployModeClient]
)


_SPARK_MEMORY_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?(?:b|k|kb|m|mb|g|gb|t|tb|p|pb)?$", re.IGNORECASE
)
_SPARK_TIME_PATTERN = re.compile(r"^\d+(?:\.\d+)?(?:us|ms|s|m|min|h|d)?$", re.IGNORECASE)


class SparkMemorySourceType(StringSourceType):
    def post_process(self, value):
        value = super().post_process(value)
        if not _SPARK_MEMORY_PATTERN.match(value):
            raise PostProcessingError(
                f"Invalid Spark memory value '{value}'. Expected a number with an optional unit "
                "(b, k, m, g, t, p)."
            )
        return value


class SparkTimeSourceType(StringSourceType):
    def post_process(self, value):
        value = super().post_process(value)
        if not _SPARK_TIME_PATTERN.match(value):
            raise PostProcessingError(
                f"Invalid Spark time value '{value}'. Expected a number with an optional unit "
                "(us, ms, s, m, min, h, d)."
            )
        return value


SparkMemory: SparkMemorySourceType = SparkMemorySourceType()
SparkTime: SparkTimeSourceType = SparkTimeSourceType()


class SparkOpError(Exception):
    pass
