from dagster import asset


@asset
def customers_table(): ...


@asset
def orders_table(): ...


@asset
def products_table(): ...
