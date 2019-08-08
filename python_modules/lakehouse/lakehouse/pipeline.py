from collections import defaultdict

from dagster import (
    DependencyDefinition,
    ModeDefinition,
    PipelineDefinition,
    ResourceDefinition,
    check,
)

from .table import LakehouseTableDefinition


def construct_lakehouse_pipeline(name, lakehouse_tables, resources, preset_defs=None):
    '''
    Dynamically construct the pipeline from the table definitions
    '''
    check.list_param(lakehouse_tables, 'lakehouse_tables', of_type=LakehouseTableDefinition)
    check.dict_param(resources, 'resources')

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

    resource_defs = {}
    for key, resource in resources.items():
        if isinstance(resource, ResourceDefinition):
            resource_defs[key] = resource
        else:
            resource_defs[key] = ResourceDefinition.hardcoded_resource(resource)

    return PipelineDefinition(
        name=name,
        mode_defs=[ModeDefinition(resource_defs=resource_defs)],
        solid_defs=lakehouse_tables,
        dependencies=dependencies,
        preset_defs=preset_defs,
    )
