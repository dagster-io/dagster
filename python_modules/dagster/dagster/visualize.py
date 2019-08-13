import graphviz

from dagster import check
from dagster.core.definitions import PipelineDefinition


def build_graphviz_graph(pipeline, only_solids):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    graphviz_graph = graphviz.Graph('pipeline', directory='/tmp/graphviz')
    for solid in pipeline.solids:
        graphviz_graph.node(solid.name)

    graphviz_graph.attr('node', color='grey', shape='box')

    if only_solids:
        for solid in pipeline.solids:
            for name in solid.input_dict.keys():
                input_handle = solid.input_handle(name)
                if pipeline.dependency_structure.has_deps(input_handle):
                    output_handles = pipeline.dependency_structure.get_deps_list(input_handle)
                    for output_handle in output_handles:
                        graphviz_graph.edge(output_handle.solid.name, solid.name)

    else:
        for solid in pipeline.solids:
            for name in solid.input_dict.keys():
                scoped_name = solid.name + '.' + name
                graphviz_graph.node(scoped_name)

        for solid in pipeline.solids:
            for name in solid.input_dict.keys():
                scoped_name = solid.name + '.' + name
                graphviz_graph.edge(scoped_name, solid.name)
                input_handle = solid.input_handle(name)
                if pipeline.dependency_structure.has_deps(input_handle):
                    output_handles = pipeline.dependency_structure.get_deps_list(input_handle)
                    for output_handle in output_handles:
                        graphviz_graph.edge(output_handle.solid.name, scoped_name)

    return graphviz_graph
