from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as context:
    context.log.info(f"Got tickers: {context.extras['tickers']}")
