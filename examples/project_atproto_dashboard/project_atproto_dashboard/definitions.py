import dagster as dg

import project_atproto_dashboard.ingestion.definitions as ingestion_definitions
import project_atproto_dashboard.modeling.definitions as modeling_definitions

defs = dg.Definitions.merge(
    ingestion_definitions.defs,
    modeling_definitions.defs,
)
