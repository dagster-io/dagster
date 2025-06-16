import dagster as dg

import project_prompt_eng.defs

defs = dg.components.load_defs(project_prompt_eng.defs)
