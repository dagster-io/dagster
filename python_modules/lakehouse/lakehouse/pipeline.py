from collections import defaultdict

from dagster import DependencyDefinition, PipelineDefinition, check
from .table import LakehouseTableDefinition


def construct_lakehouse_pipeline(name, lakehouse_tables, mode_defs=None):
    '''
    Dynamically construct the pipeline from the table definitions
    '''
    check.list_param(lakehouse_tables, 'lakehouse_tables', of_type=LakehouseTableDefinition)

    type_to_solid = {}
    for lakehouse_table in lakehouse_tables:
        output_type_name = lakehouse_table.output_defs[0].runtime_type.name
        check.invariant(
            output_type_name not in type_to_solid,
            'Duplicate Lakehouse output names "{}"'.format(output_type_name),
        )
        type_to_solid[output_type_name] = lakehouse_table

    dependencies = defaultdict(dict)

    for lakehouse_table in lakehouse_tables:
        for input_def in lakehouse_table.input_tables:
            input_type_name = input_def.runtime_type.name
            check.invariant(input_type_name in type_to_solid)
            dependencies[lakehouse_table.name][input_def.name] = DependencyDefinition(
                type_to_solid[input_type_name].name
            )

    return PipelineDefinition(
        name=name, mode_defs=mode_defs, solid_defs=lakehouse_tables, dependencies=dependencies
    )
