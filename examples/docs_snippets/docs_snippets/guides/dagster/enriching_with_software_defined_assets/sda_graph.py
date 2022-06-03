from pandas import DataFrame

from dagster import AssetSelection, AssetsDefinition, GraphOut, graph, op, repository

from .mylib import create_db_connection, fetch_products


@op
def extract_products() -> DataFrame:
    return fetch_products()


@op
def get_categories(products: DataFrame) -> DataFrame:
    return DataFrame({"category": products["category"].unique()})


@op
def write_products_table(products: DataFrame) -> None:
    products.to_sql(name="categories", con=create_db_connection())


@op
def write_categories_table(categories: DataFrame) -> None:
    categories.to_sql(name="categories", con=create_db_connection())


@graph(out={"products": GraphOut(), "categories": GraphOut()})
def ingest_graph():
    products = extract_products()
    product_categories = get_categories(products)
    return write_products_table(products), write_categories_table(product_categories)


two_tables = AssetsDefinition.from_graph(ingest_graph)


@repository
def repo():
    return [two_tables, AssetSelection.all().to_job("products_and_categories")]
