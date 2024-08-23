from pathlib import Path

IRIS_COLUMNS = [
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
    "species",
]


def shared_folder() -> Path:
    return Path(__file__).parent


DB_PATH = shared_folder() / "jaffle_shop.duckdb"
CSV_PATH = shared_folder() / "iris.csv"
