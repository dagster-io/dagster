from dagster.visualize import build_graphviz_graph

from .core_tests.engine_tests.test_multiprocessing import define_diamond_pipeline


def test_graphviz():
    build_graphviz_graph(define_diamond_pipeline(), [])
    build_graphviz_graph(define_diamond_pipeline(), ['mult_three'])
