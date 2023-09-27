from dagster_pipes import init_dagster_pipes

context = init_dagster_pipes()

context.log.info(f"Got tickers: {context.extras['tickers']}")
