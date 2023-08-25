from dagster_externals import init_dagster_externals

context = init_dagster_externals()

context.log(f"Got tickers: {context.extras['tickers']}")
