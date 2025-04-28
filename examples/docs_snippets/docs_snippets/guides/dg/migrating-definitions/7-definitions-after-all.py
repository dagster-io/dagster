import dagster as dg
import my_existing_project.defs

defs = dg.components.load_defs(my_existing_project.defs)
