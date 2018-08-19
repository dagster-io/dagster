import jinja2

from dagster import (
    ArgumentDefinition,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)

from .common import execute_sql_text_on_context


def create_templated_sql_transform_solid(name, sql, table_arguments, dependant_solids=None):
    check.str_param(name, 'name')
    check.str_param(sql, 'sql')
    check.list_param(table_arguments, 'table_arguments', of_type=str)

    dependant_solids = check.opt_list_param(
        dependant_solids, 'dependant_solids', of_type=SolidDefinition
    )

    config_def = {}
    for table in table_arguments:
        config_def[table] = ArgumentDefinition(types.String)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition(solid.name) for solid in dependant_solids],
        config_def=config_def,
        transform_fn=_create_templated_sql_transform_with_output(sql),
        outputs=[OutputDefinition()],
    )


def _render_template_string(template_text, config_dict):
    template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(template_text)
    return template.render(**config_dict)


def _create_templated_sql_transform_with_output(sql):
    def do_transform(context, _inputs, config_dict):
        rendered_sql = _render_template_string(sql, config_dict)
        execute_sql_text_on_context(context, rendered_sql)
        yield Result(config_dict)

    return do_transform
