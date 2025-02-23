import dagster as dg


@dg.asset
def customers_table(): ...


@dg.asset
def orders_table(): ...


@dg.asset
def products_table(): ...
