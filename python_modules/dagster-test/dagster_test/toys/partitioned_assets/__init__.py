from .different_static_partitions import (
    static_partitioned_asset1,
    static_partitioned_asset2,
)
from .dynamic_asset_partitions import (
    defs as dynamic_asset_partition_defs,
)

from .failing_partitions import (
    failing_time_partitioned,
    failing_static_partitioned,
    downstream_of_failing_partitioned,
)

from .hourly_and_daily_and_unpartitioned import (
    daily_partitions_def,
    upstream_daily_partitioned_asset,
    downstream_daily_partitioned_asset,
    hourly_partitioned_asset,
    unpartitioned_asset,
)

from .single_partitions_to_multi import composite, abc_def, multi_partitions, single_partitions
