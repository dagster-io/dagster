from typing import Callable

import dagster as dg


class MyComponent(dg.Component):
    @staticmethod
    @dg.template_var
    def database_url() -> str:
        """Static template variable - no context needed."""
        return "postgresql://localhost:5432/mydb"

    @staticmethod
    @dg.template_var
    def component_table_name(context: dg.ComponentLoadContext) -> str:
        """Context-aware template variable - uses component path."""
        return f"table_{context.path.name}"

    @staticmethod
    @dg.template_var
    def environment_config(context: dg.ComponentLoadContext) -> dict:
        """Context-aware template variable returning complex object."""
        return {
            "component_name": context.path.name,
            "timeout": 30,
            "retries": 3,
        }

    @staticmethod
    @dg.template_var
    def table_name_generator() -> Callable[[str], str]:
        """Static template variable returning a function (UDF)."""
        return lambda prefix: f"{prefix}_processed_data"

    @staticmethod
    @dg.template_var
    def context_aware_generator(
        context: dg.ComponentLoadContext,
    ) -> Callable[[str], str]:
        """Context-aware template variable returning a function (UDF)."""
        component_prefix = context.path.name
        return lambda suffix: f"{component_prefix}_{suffix}"
