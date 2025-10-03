import dagster as dg

import project_dspy.defs as definitions
from project_dspy.defs import resources

defs = dg.Definitions.merge(
    dg.components.load_defs(definitions),
    dg.Definitions(
        resources={
            "gemini": resources.gemini_resource,
            "dspy_resource": resources.dspy_resource,
        },
    ),
)
