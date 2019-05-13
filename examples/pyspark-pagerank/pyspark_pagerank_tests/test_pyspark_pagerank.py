import pyspark_pagerank

from pyspark_pagerank.repository import define_repository


def test_pyspark_pagerank_repo():
    assert define_repository().get_all_pipelines()
