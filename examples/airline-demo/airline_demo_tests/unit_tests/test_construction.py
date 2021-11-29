import pytest
from airline_demo.pipelines import (
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)


def test_construct_ingest_pipeline():
    assert define_airline_demo_ingest_pipeline()


@pytest.mark.skipif('"win" in sys.platform', reason="avoiding the geopandas tests")
def test_construct_warehouse_pipeline():
    assert define_airline_demo_warehouse_pipeline()
