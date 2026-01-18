import dagster as dg


def add_partitions_def(spec: dg.AssetSpec) -> dg.AssetSpec:
    return spec.replace_attributes(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01")
    )


class ExampleComponentWithPartitions(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Use map_asset_specs to add a property to all assets
        return super().build_defs(context).map_asset_specs(add_partitions_def)
