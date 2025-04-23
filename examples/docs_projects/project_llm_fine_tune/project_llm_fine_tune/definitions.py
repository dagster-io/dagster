import dagster as dg

import project_llm_fine_tune.defs

defs = dg.Definitions.merge(
    dg.components.load_defs(project_llm_fine_tune.defs),
)
