from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    pipes.log.info(f"Got tickers: {pipes.extras['tickers']}")
