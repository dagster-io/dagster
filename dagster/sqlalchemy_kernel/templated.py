import jinja2

import dagster
from dagster import check
from dagster.core.definitions import (Solid, InputDefinition)

from .common import execute_sql_text_on_context


def _create_table_input(name, depends_on=None):
    return InputDefinition(
        name=name,
        input_fn=lambda arg_dict: arg_dict,
        argument_def_dict={'name': dagster.core.types.STRING},
        depends_on=depends_on
    )


def create_templated_sql_transform_solid(name, sql, table_arguments, dependencies, output):
    check.str_param(name, 'name')
    check.str_param(sql, 'sql')
    check.list_param(table_arguments, 'table_arguments', of_type=str)
    check.list_param(dependencies, 'dependencies', of_type=Solid)
    check.str_param(output, 'output')

    table_inputs = [_create_table_input(table) for table in table_arguments]
    dep_inputs = [_create_table_input(dep.name, depends_on=dep) for dep in dependencies]
    return Solid(
        name=name,
        inputs=table_inputs + dep_inputs,
        transform_fn=_create_templated_sql_transform_with_output(sql, output),
        outputs=[],
    )


def _render_template_string(template_text, **kwargs):
    template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(template_text)
    return template.render(**kwargs)


def _create_templated_sql_transform_with_output(sql, output_table):
    def do_transform(context, **kwargs):
        rendered_sql = _render_template_string(sql, **kwargs)
        execute_sql_text_on_context(context, rendered_sql)
        return kwargs[output_table]

    return do_transform
