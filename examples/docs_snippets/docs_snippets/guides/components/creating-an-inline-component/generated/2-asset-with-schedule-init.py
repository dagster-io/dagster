import dagster as dg

class AssetWithSchedule(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
