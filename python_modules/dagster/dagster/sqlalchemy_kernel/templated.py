import jinja2

import dagster
from dagster import check
from dagster.core.definitions import (
    SolidDefinition,
    InputDefinition,
    SourceDefinition,
    ArgumentDefinition,
)

from .common import execute_sql_text_on_context


def _create_table_input(name, depends_on=None):
    return InputDefinition(
        name=name,
        sources=[
            SourceDefinition(
                source_type='TABLENAME',
                source_fn=lambda context, arg_dict: arg_dict,
                argument_def_dict={'name': ArgumentDefinition(dagster.core.types.String)},
            )
        ],
        depends_on=depends_on
    )


def create_templated_sql_transform_solid(
    name,
    sql,
    table_arguments,
    output,
    dependencies=None,
    extra_inputs=None,
):
    '''
    Create a solid that is a templated sql statement. This assumes that the sql statement
    is creating or modifying a table, and that that table will be used downstream in the pipeline
    for further transformations

    Usage example:

    sum_sql_template = 'CREATE TABLE {{sum_table.name}} AS ' + \
        'SELECT num1, num2, num1 + num2 as sum FROM {{num_table.name}}'

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sum_sql_template,
        table_arguments=['sum_table', 'num_table'],
        output='sum_table',
    )

    'Table arguments' are inputs that represent a table. They have a string property "name". Each
    table argument ends up as an InputDefinition into the solid.

    To invoke this you would configure an argument dictionary to look like:

    input_arg_dict = {'sum_table': {'name': 'a_sum_table'}, 'num_table': {'name': 'a_num_table'}}

    dagster.execute_pipeline(context, pipeline, input_arg_dict)

    The output table is what is flowed to the *next* solid.

    So imagine, we built another solid which depended on the previous one.

    sum_sq_sql_template = 'CREATE TABLE {{sum_sq_table.name}} AS ' + \
        'SELECT num1, num2, sum, sum * sum as sum_sq FROM {{sum_solid.name}}'

    sum_sq_solid = create_templated_sql_transform_solid(
        name='sum_sq_solid',
        sql=sum_sq_sql_template,
        table_arguments=['sum_sq_table'],
        output='sum_sq_table',
        dependencies=[sum_solid],
    )

    This solid has two inputs, one is a table_argument directly passed in, and one is
    the table from the previous solid.

    Note: there is current awkwardness in this api because all inputs and solids in pipeline
    must have a different name. This is why the template variable in the "sum_sq_solid" is
    named "sum_solid" rather than "sum_table".

    To invoke this you would now specifiy:

    input_arg_dict = {
        'sum_table': {'name': 'a_sum_table'},
        'num_table': {'name': 'a_num_table'},
        'sum_sq_table': {'name': 'a_sum_sq_table'},
    }

    If you wanted to test the sum_sq_table in isolation, you could skip the num_table and just
    specify the output of the sum_solid:

    input_arg_dict = {
        'sum_solid': {'name': 'a_sum_table'},
        'sum_sq_table': {'name': 'a_sum_sq_table'},
    }

    As noted above the naming is not very intuitive right row, but the functionality works.
    '''
    check.str_param(name, 'name')
    check.str_param(sql, 'sql')
    check.list_param(table_arguments, 'table_arguments', of_type=str)
    check.str_param(output, 'output')
    dependencies = check.opt_list_param(dependencies, 'dependencies', of_type=SolidDefinition)
    extra_inputs = check.opt_list_param(extra_inputs, 'extra_inputs', of_type=InputDefinition)

    table_inputs = [_create_table_input(table) for table in table_arguments]
    dep_inputs = [_create_table_input(dep.name, depends_on=dep) for dep in dependencies]
    return SolidDefinition(
        name=name,
        inputs=table_inputs + dep_inputs + extra_inputs,
        transform_fn=_create_templated_sql_transform_with_output(sql, output),
        output=dagster.OutputDefinition(),
    )


def _render_template_string(template_text, args):
    template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(template_text)
    return template.render(**args)


def _create_templated_sql_transform_with_output(sql, output_table):
    def do_transform(context, args):
        rendered_sql = _render_template_string(sql, args)
        execute_sql_text_on_context(context, rendered_sql)
        return args[output_table]

    return do_transform
