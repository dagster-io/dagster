import dagster as dg


class AssetFactory(dg.Component, dg.Model, dg.Resolvable):
    # highlight-start
    department: str = dg.Field
    # highlight-end

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(
            name=f"{self.department}_import",
        )
        def _import_data(context: dg.AssetExecutionContext) -> None: ...

        @dg.asset(
            deps=[_import_data],
            name=f"{self.department}_process",
        )
        def _process_data(context: dg.AssetExecutionContext) -> None: ...

        return dg.Definitions(assets=[_import_data, _process_data])
