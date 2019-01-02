import json

from dagster import check

from .configurable import (
    Field,
    ConfigurableSelectorFromDict,
)


class Materializeable(object):
    def define_materialization_config_schema(self):
        check.failed('must implement')

    def materialize_runtime_value(self, _config_spec, _runtime_value):
        check.failed('must implement')


class MaterializeableBuiltinScalar(Materializeable):
    def define_materialization_config_schema(self):
        # TODO: reorganie types to avoid circular deps
        from .types import MaterializeableBuiltinScalarConfigSchema

        # pylint: disable=E1101
        # For now assuming all Materializalbes are Types and have names available
        return MaterializeableBuiltinScalarConfigSchema(self.name)

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


class FileMarshalable:
    def marshal_value(self, _value, _to_file):
        check.not_implemented('must implement')

    def unmarshal_value(self, _from_file):
        check.not_implemented('must implement')
