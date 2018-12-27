import json

from dagster import check

from .configurable import (
    Field,
    ConfigurableSelectorFromDict,
)


def define_path_dict_field():
    from .types import (
        Dict,
        Path,
    )
    return Field(Dict({'path': Field(Path)}))


class Materializeable(object):
    def define_materialization_config_schema(self):
        check.failed('must implement')

    def materialize_runtime_value(self, _config_spec, _runtime_value):
        check.failed('must implement')


class MaterializeableValueConfigSchema(ConfigurableSelectorFromDict):
    def __init__(self):
        # TODO: add pickle
        super(
            MaterializeableValueConfigSchema,
            self,
        ).__init__(fields={'json': define_path_dict_field()})

    def iterate_types(self):
        return []


class MaterializeableValue(Materializeable):
    def define_materialization_config_schema(self):
        return MaterializeableValueConfigSchema()

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
