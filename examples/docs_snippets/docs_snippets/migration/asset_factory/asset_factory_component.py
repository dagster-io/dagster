import dagster as dg


class AssetFactory(dg.Component, dg.Model, dg.Resolvable):
    # highlight-start
    departments: list[str] = dg.Field
    # highlight-end

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        _assets = []

        for department in self.departments:

            @dg.asset(
                name=f"{department}_import",
            )
            def _import_data(context: dg.AssetExecutionContext) -> None: ...

            @dg.asset(
                deps=[_import_data],
                name=f"{department}_process",
            )
            def _process_data(context: dg.AssetExecutionContext) -> None: ...

            _assets.extend([_import_data, _process_data])

        # highlight-start
        return dg.Definitions(assets=_assets)

    # highlight-end
