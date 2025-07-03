from dagster._core.definitions.partitions.definition.dynamic import (
    DynamicPartitionsDefinition as DynamicPartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.multi import (
    MultiPartitionsDefinition as MultiPartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition as PartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.static import (
    StaticPartitionsDefinition as StaticPartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.time_window import (
    TimeWindowPartitionsDefinition as TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.time_window_subclasses import (
    DailyPartitionsDefinition as DailyPartitionsDefinition,
    HourlyPartitionsDefinition as HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition as MonthlyPartitionsDefinition,
    WeeklyPartitionsDefinition as WeeklyPartitionsDefinition,
)
