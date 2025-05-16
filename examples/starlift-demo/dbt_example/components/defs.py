import dagster as dg
from dagster.components import load_defs

from dbt_example.components import (
    federated_instance_1 as federated_instance_1,
    federated_instance_2 as federated_instance_2,
    migrating_instance as migrating_instance,
)

defs = dg.Definitions.merge(
    *[
        load_defs(defs_root=m)
        for m in [migrating_instance, federated_instance_1, federated_instance_2]
    ]
)
