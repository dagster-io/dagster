import dagster as dg


class MyComponent(dg.Component):
    a_string: str
    an_int: int

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
