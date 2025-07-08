import dagster as dg


# start_asset_factory
def asset_factory(department: str) -> dg.Definitions:
    _assets = []

    @dg.asset(
        name=f"{department}_import",
    )
    def _import_data(context: dg.AssetExecutionContext) -> None: ...

    @dg.asset(
        deps=[_import_data],
        name=f"{department}_process",
    )
    def _process_data(context: dg.AssetExecutionContext) -> None: ...

    # highlight-start
    return dg.Definitions(
        assets=[
            _import_data,
            _process_data,
        ]
    )
    # highlight-end


# end_asset_factory


# start_defs
@dg.definitions
def defs() -> dg.Definitions:
    departments = ["engineering", "marketing", "sales"]

    return dg.Definitions.merge(
        *[asset_factory(department) for department in departments]
    )


# end_defs
