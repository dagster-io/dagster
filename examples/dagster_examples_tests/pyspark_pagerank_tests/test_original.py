import os

from dagster_examples.pyspark_pagerank.original import (
    computeContribs,
    execute_pagerank,
    parseNeighbors,
)
from .util import checks_for_helper_functions


def test_helpers():
    checks_for_helper_functions(computeContribs, parseNeighbors)


def test_execute_pagerank():
    cwd = os.path.dirname(__file__)

    result = execute_pagerank(os.path.join(cwd, 'pagerank_data.txt'), 2)
    assert set(result) == {
        ('anotherlessimportantsite.com', 0.9149999999999999),
        ('whatdoesitallmeananyways.com', 0.9149999999999999),
        ('importantsite.com', 1.255),
        ('alessimportantsite.com', 0.9149999999999999),
    }
