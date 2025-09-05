import os

import dagster as dg


@dg.template_var
def table_prefix() -> str:
    if os.getenv("IS_PROD"):
        return "warehouse"
    else:
        return "staging"
