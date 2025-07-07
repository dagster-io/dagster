import dagster as dg


class MyYamlComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(
            assets=[dg.AssetSpec(key=dg.AssetKey(["foo"]))],
        )
