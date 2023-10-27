from pandas import DataFrame

from dagster import Definitions, job, op

from .mylib import create_db_connection, fetch_products


@op
def extract_products() -> DataFrame:
    return fetch_products()


@op
def get_categories(products: DataFrame) -> DataFrame:
    return DataFrame({"category": products["category"].unique()})


@op
def write_products_table(products: DataFrame) -> None:
    products.to_sql(name="products", con=create_db_connection())


@op
def write_categories_table(categories: DataFrame) -> None:
    categories.to_sql(name="categories", con=create_db_connection())


@job
def ingest_products_and_categories():
    products = extract_products()
    product_categories = get_categories(products)
    return write_products_table(products), write_categories_table(product_categories)


defs = Definitions(
    jobs=[ingest_products_and_categories],
)
