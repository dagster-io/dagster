from dagster import (
    InputDefinition,
    Output,
    OutputDefinition,
    PythonObjectDagsterType,
    SolidDefinition,
    check,
)
from dagster.core.definitions.decorators import validate_solid_fn

from .house import Lakehouse


class ITableHandle(object):
    pass


class TableHandle(ITableHandle):
    pass


class InMemTableHandle(ITableHandle):
    def __init__(self, value):
        self.value = value


class LakehouseTableDefinition(SolidDefinition):
    '''
    Trivial subclass, only useful for typehcecks and to implement table_type.
    '''

    def __init__(self, lakehouse_fn, output_defs, input_tables, input_defs, **kwargs):
        check.list_param(output_defs, 'output_defs', OutputDefinition)
        check.param_invariant(len(output_defs) == 1, 'output_defs')
        input_tables = check.opt_list_param(
            input_tables, input_tables, of_type=LakehouseTableInputDefinition
        )
        input_defs = check.opt_list_param(input_defs, input_defs, of_type=InputDefinition)

        self.lakehouse_fn = lakehouse_fn
        self.input_tables = input_tables
        super(LakehouseTableDefinition, self).__init__(
            output_defs=output_defs, input_defs=input_defs, **kwargs
        )

    @property
    def table_type(self):
        return self.output_defs[0].runtime_type


def create_lakehouse_table_def(
    name,
    lakehouse_fn,
    input_tables=None,
    other_input_defs=None,
    required_resource_keys=None,
    tags=None,
    description=None,
):
    input_tables = check.opt_list_param(
        input_tables, input_tables, of_type=LakehouseTableInputDefinition
    )
    other_input_defs = check.opt_list_param(
        other_input_defs, other_input_defs, of_type=InputDefinition
    )
    required_resource_keys = check.opt_set_param(
        required_resource_keys, 'required_resource_keys', of_type=str
    )

    table_type = PythonObjectDagsterType(
        python_type=ITableHandle, name=name, description=description
    )

    table_input_dict = {input_table.name: input_table for input_table in input_tables}
    input_defs = input_tables + other_input_defs
    validate_solid_fn('@solid', name, lakehouse_fn, input_defs, ['context'])

    def _compute(context, inputs):
        '''
        Workhouse function of lakehouse. The inputs are something that inherits from ITableHandle.
        This compute_fn:
        (1) Iterates over input tables and ask the lakehouse resource to
         hydrate their contents or a representation of their contents
         (e.g a pyspark dataframe) into memory for computation
        (2) Pass those into the lakehouse table function. Do the actual thing.
        (3) Pass the output of the lakehouse function to the lakehouse materialize function.
        (4) Yield a materialization if the lakehouse function returned that.


        There's an argument that the hydrate and materialize functions should return
        a stream of events but that started to feel like I was implementing what should
        be a framework feature.
        '''
        check.inst_param(context.resources.lakehouse, 'context.resources.lakehouse', Lakehouse)

        # hydrate tables
        hydrated_tables = {}
        other_inputs = {}
        for input_name, value in inputs.items():
            context.log.info(
                'About to hydrate table {input_name} for use in {name}'.format(
                    input_name=input_name, name=name
                )
            )
            if input_name in table_input_dict:
                table_handle = value
                input_type = table_input_dict[input_name].runtime_type
                hydrated_tables[input_name] = context.resources.lakehouse.hydrate(
                    context,
                    input_type,
                    table_def_of_type(context.pipeline_def, input_type.name).tags,
                    table_handle,
                    tags,
                )
            else:
                other_inputs[input_name] = value

        # call user-provided business logic which operates on the hydrated values
        # (as opposed to the handles)
        computed_output = lakehouse_fn(context, **hydrated_tables, **other_inputs)

        materialization, output_table_handle = context.resources.lakehouse.materialize(
            context, table_type, tags, computed_output
        )

        if materialization:
            yield materialization

        # just pass in a dummy handle for now if the materialize function
        # does not return one
        yield Output(output_table_handle if output_table_handle else TableHandle())

    required_resource_keys.add('lakehouse')

    return LakehouseTableDefinition(
        lakehouse_fn=lakehouse_fn,
        name=name,
        input_tables=input_tables,
        input_defs=input_defs,
        output_defs=[OutputDefinition(table_type)],
        compute_fn=_compute,
        required_resource_keys=required_resource_keys,
        tags=tags,
        description=description,
    )


def table_def_of_type(pipeline_def, type_name):
    for solid_def in pipeline_def.all_solid_defs:
        if (
            isinstance(solid_def, LakehouseTableDefinition)
            and solid_def.table_type.name == type_name
        ):
            return solid_def


class LakehouseTableInputDefinition(InputDefinition):
    def __init__(self, name, lakehouse_table_def):
        check.str_param(name, 'name')
        check.inst_param(lakehouse_table_def, 'lakehouse_table_def', LakehouseTableDefinition)

        self.table_def = lakehouse_table_def

        super(LakehouseTableInputDefinition, self).__init__(
            name,
            dagster_type=lakehouse_table_def.table_type,
            description=lakehouse_table_def.description,
        )


def input_table(name, lakehouse_table_def):
    return LakehouseTableInputDefinition(name, lakehouse_table_def)
