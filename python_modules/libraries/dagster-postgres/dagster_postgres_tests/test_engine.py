import pytest
from dagster_postgres.utils import create_pg_engine


@pytest.mark.parametrize(
    "url, driver",
    [
        ("postgresql://user:pass@localhost:5432/db", "psycopg2"),
        ("postgresql+psycopg2://user:pass@localhost:5432/db", "psycopg2"),
    ],
)
def test_engine_driver(url: str, driver: str):
    engine = create_pg_engine(url)
    assert engine.dialect.driver == driver
