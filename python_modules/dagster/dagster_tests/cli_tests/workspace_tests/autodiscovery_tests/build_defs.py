from dagster import Definitions, DefinitionsLoadContext, asset, defs_loader


@defs_loader
def defs(context: DefinitionsLoadContext) -> Definitions:
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
