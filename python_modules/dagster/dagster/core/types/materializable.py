import json

from dagster import check

from .configurable import (
    ConfigurableSelectorFromDict,
    Field,
)


def define_path_dict_field():
    from . import Dict, Path
    return Field(Dict({'path': Field(Path)}))


class Materializeable(object):
    def define_materialization_config_schema(self):
        check.failed('must implement')

    def materialize_runtime_value(self, _config_spec, _runtime_value):
        check.failed('must implement')


class MaterializeableBuiltinScalarConfigSchema(ConfigurableSelectorFromDict):
    def __init__(self, name):
        # TODO: add pickle
        super(
            MaterializeableBuiltinScalarConfigSchema,
            self,
        ).__init__(fields={'json': define_path_dict_field()})
        self.name = name
        self.description = 'Materialization schema for scalar ' + name

    def iterate_types(self):
        yield self


class MaterializeableBuiltinScalar(Materializeable):
    def __init__(self, *args, **kwargs):
        super(MaterializeableBuiltinScalar, self).__init__(*args, **kwargs)
        self.config_schema = None

    def define_materialization_config_schema(self):
        if self.config_schema is None:
            # This has to be applied to a dagster type so name is available
            # pylint: disable=E1101
            self.config_schema = MaterializeableBuiltinScalarConfigSchema(
                '{name}.MaterializationSchema'.format(name=self.name)
            )
        return self.config_schema

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
