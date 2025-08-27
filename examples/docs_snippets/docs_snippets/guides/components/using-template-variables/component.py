from typing import Callable

import dagster as dg


class MyComponent(dg.Component):
    @staticmethod
    @dg.template_var
    def database_url() -> str:
        return "postgresql://localhost:5432/mydb"

    @staticmethod
    @dg.template_var
    def get_table_name() -> Callable:
        return lambda prefix: f"{prefix}_processed_data"
