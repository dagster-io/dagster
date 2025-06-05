import dagster as dg

import project_atproto_dashboard.defs
from project_atproto_dashboard.defs.resources import (
    atproto_resource,
    dbt_resource,
    power_bi_workspace,
    s3_resource,
)

# start_def
defs = dg.Definitions.merge(
    dg.components.load_defs(project_atproto_dashboard.defs),
    dg.Definitions(
        resources={
            "dbt": dbt_resource,
            "power_bi": power_bi_workspace,
            "atproto_resource": atproto_resource,
            "s3_resource": s3_resource,
        }
    ),
)
# end_def
