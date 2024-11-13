from enum import Enum
from typing import Optional

from schema.charts.utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class SchedulerType(str, Enum):
    DAEMON = "DagsterDaemonScheduler"
    CUSTOM = "CustomScheduler"


class DaemonSchedulerConfig(BaseModel):
    maxCatchupRuns: Optional[int] = None
    maxTickRetries: Optional[int] = None


class SchedulerConfig(BaseModel, extra="forbid"):
    daemonScheduler: Optional[DaemonSchedulerConfig] = None
    customScheduler: Optional[ConfigurableClass] = None


class Scheduler(
    BaseModel,
    extra="forbid",
    json_schema_extra={
        "allOf": create_json_schema_conditionals({SchedulerType.CUSTOM: "customScheduler"})
    },
):
    type: SchedulerType
    config: SchedulerConfig
