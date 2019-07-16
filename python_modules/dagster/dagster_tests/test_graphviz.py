from dagster import lambda_solid, pipeline
from dagster.visualize import build_graphviz_graph

from .core_tests.engine_tests.test_multiprocessing import define_diamond_pipeline


@lambda_solid
def single_input_solid(_x):
    return


@pipeline
def single_input_solid_pipeline():
    return [single_input_solid.alias('foo')(), single_input_solid.alias('bar')()]


def test_graphviz():
    build_graphviz_graph(define_diamond_pipeline(), [])
    build_graphviz_graph(define_diamond_pipeline(), ['mult_three'])
    build_graphviz_graph(single_input_solid_pipeline, [])
    build_graphviz_graph(single_input_solid_pipeline, ['single_input_solid'])
