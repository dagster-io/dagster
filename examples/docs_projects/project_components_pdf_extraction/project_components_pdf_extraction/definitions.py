from dagster.components import load_defs

import project_components_pdf_extraction.defs

defs = load_defs(defs_root=project_components_pdf_extraction.defs)
