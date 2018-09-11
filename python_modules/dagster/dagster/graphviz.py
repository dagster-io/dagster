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
            for input_def in solid.input_defs:
                input_handle = solid.input_handle(input_def.name)
                if pipeline.dependency_structure.has_dep(input_handle):
                    output_handle = pipeline.dependency_structure.get_dep(input_handle)
                    graphviz_graph.edge(output_handle.solid.name, solid.name)

    else:
        for solid in pipeline.solids:
            for input_def in solid.input_defs:
                scoped_name = solid.name + '.' + input_def.name
                graphviz_graph.node(scoped_name)

        for solid in pipeline.solids:
            for input_def in solid.input_defs:
                scoped_name = solid.name + '.' + input_def.name
                graphviz_graph.edge(scoped_name, solid.name)
                input_handle = solid.input_handle(input_def.name)
                if pipeline.dependency_structure.has_dep(input_handle):
                    output_handle = pipeline.dependency_structure.get_dep(input_handle)
                    graphviz_graph.edge(output_handle.solid.name, scoped_name)

    return graphviz_graph
