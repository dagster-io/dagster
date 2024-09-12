import dagster as dg


@dg.asset
def hello(context: dg.AssetExecutionContext):
    context.log.info("Hello!")


@dg.asset
def world(context: dg.AssetExecutionContext):
    context.log.info("World!")


defs = dg.Definitions(assets=[hello, world])

if __name__ == "__main__":
    dg.materialize(hello)
    dg.materialize(world)
