from enum import Enum

from schema.charts.utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class SchedulerType(str, Enum):
    DAEMON = "DagsterDaemonScheduler"
    CUSTOM = "CustomScheduler"


class DaemonSchedulerConfig(BaseModel):
    maxCatchupRuns: int | None = None
    maxTickRetries: int | None = None


class SchedulerConfig(BaseModel, extra="forbid"):
    daemonScheduler: DaemonSchedulerConfig | None = None
    customScheduler: ConfigurableClass | None = None


class Scheduler(
    BaseModel,
    extra="forbid",
    json_schema_extra={
        "allOf": create_json_schema_conditionals({SchedulerType.CUSTOM: "customScheduler"})
    },
):
    type: SchedulerType
    config: SchedulerConfig
