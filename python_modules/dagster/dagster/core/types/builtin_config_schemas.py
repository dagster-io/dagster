import json

from dagster import check

from .builtin_enum import BuiltinEnum
from .field import ConfigSelector, Field, Dict


def define_path_dict_field():
    return Field(Dict({'path': Field(BuiltinEnum.PATH)}))


def define_builtin_scalar_output_schema(scalar_name):
    check.str_param(scalar_name, 'scalar_name')

    class _MaterializeableBuiltinScalarConfigSchema(ConfigSelector):
        def __init__(self):
            super(_MaterializeableBuiltinScalarConfigSchema, self).__init__(
                name=scalar_name + '.MaterializationSchema',
                description='Materialization schema for scalar ' + scalar_name,
                fields={'json': define_path_dict_field()},
            )

        def materialize_runtime_value(self, config_spec, runtime_value):
            check.dict_param(config_spec, 'config_spec')
            selector_key, selector_value = list(config_spec.items())[0]

            if selector_key == 'json':
                json_file_path = selector_value['path']
                json_value = json.dumps({'value': runtime_value})
                with open(json_file_path, 'w') as ff:
                    ff.write(json_value)
            else:
                check.failed(
                    'Unsupported selector key: {selector_key}'.format(selector_key=selector_key)
                )

    return _MaterializeableBuiltinScalarConfigSchema
