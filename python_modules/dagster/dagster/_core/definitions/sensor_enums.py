from enum import Enum

from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class DefaultSensorStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


@whitelist_for_serdes
class SensorType(Enum):
    STANDARD = "STANDARD"
    RUN_STATUS = "RUN_STATUS"
    ASSET = "ASSET"
    MULTI_ASSET = "MULTI_ASSET"
    FRESHNESS_POLICY = "FRESHNESS_POLICY"
    AUTO_MATERIALIZE = "AUTO_MATERIALIZE"
    UNKNOWN = "UNKNOWN"


DEFAULT_SENSOR_DAEMON_INTERVAL = 30
