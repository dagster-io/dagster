from dagster_pipes import init_dagster_pipes_process

context = init_dagster_pipes_process()

context.log(f"Got tickers: {context.extras['tickers']}")
