import json
import os

import jinja2

from dagster import (
    ConfigDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)

from .common import execute_sql_text_on_context


class DagsterSqlTextType(types.DagsterStringType):
    def __init__(self):
        super(DagsterSqlTextType, self).__init__(
            name='SqlText',
            description='A string of SQL text that is directly executable.',
        )

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(self.evaluate_value(value), output_dir)
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump(
                {
                    'type': type_value.name,
                    'value': type_value.value,
                },
                ff,
            )

        with open(os.path.join(output_dir, 'sql'), 'w') as sf:
            sf.write(value)


SqlTextType = DagsterSqlTextType()


def create_templated_sql_transform_solid(name, sql, table_arguments, dependant_solids=None):
    check.str_param(name, 'name')
    check.str_param(sql, 'sql')
    check.list_param(table_arguments, 'table_arguments', of_type=str)

    dependant_solids = check.opt_list_param(
        dependant_solids, 'dependant_solids', of_type=SolidDefinition
    )

    field_dict = {}
    for table in table_arguments:
        field_dict[table] = Field(types.String)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition(solid.name) for solid in dependant_solids],
        config_def=ConfigDefinition.config_dict('{name}_Type'.format(name=name), field_dict),
        transform_fn=_create_templated_sql_transform_with_output(sql),
        outputs=[
            OutputDefinition(name='result', dagster_type=types.Any),
            OutputDefinition(name='sql_text', dagster_type=SqlTextType),
        ],
    )


def _render_template_string(template_text, config_dict):
    template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(template_text)
    return template.render(**config_dict)


def _create_templated_sql_transform_with_output(sql):
    def do_transform(info, _inputs):
        rendered_sql = _render_template_string(sql, info.config)
        execute_sql_text_on_context(info.context, rendered_sql)
        yield Result(info.config)
        yield Result(output_name='sql_text', value=rendered_sql)

    return do_transform
