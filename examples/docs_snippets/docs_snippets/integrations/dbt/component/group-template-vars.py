from collections.abc import Callable, Sequence
from typing import Optional

import dagster as dg


@dg.template_var
def group_from_fqn() -> Callable[[Sequence[str]], str | None]:
    """Returns a function that extracts the group name from a dbt model's fqn.

    The fqn (fully qualified name) contains the directory structure, e.g.:
    ["jaffle_shop", "staging", "stg_customers"] -> returns "staging"
    ["jaffle_shop", "marts", "customers"] -> returns "marts"
    """

    def _get_group(fqn: Sequence[str]) -> str | None:
        # fqn structure: [project_name, folder, ..., model_name]
        # We want the first folder after the project name
        if len(fqn) >= 2:
            return fqn[1]  # Returns "staging", "intermediate", "marts", etc.
        return None

    return _get_group
