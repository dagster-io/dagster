import graphviz

import check

from solidic.graph import SolidPipeline


def build_graphviz_graph(pipeline):
    check.inst_param(pipeline, 'pipeline', SolidPipeline)
    graphviz_graph = graphviz.Graph('pipeline', directory='/tmp/graphviz')
    for solid in pipeline.solids:
        graphviz_graph.node(solid.name)

    graphviz_graph.attr('node', color='grey')

    for input_def in pipeline.external_inputs:
        graphviz_graph.node(input_def.name)

    for solid in pipeline.solids:
        for input_def in solid.inputs:
            graphviz_graph.edge(input_def.name, solid.name)

    return graphviz_graph
