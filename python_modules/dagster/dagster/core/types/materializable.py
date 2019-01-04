from dagster import check


class Materializeable(object):
    def define_materialization_config_schema(self):
        check.failed('must implement')

    def materialize_runtime_value(self, _config_spec, _runtime_value):
        check.failed('must implement')


class FileMarshalable:
    def marshal_value(self, _value, _to_file):
        check.not_implemented('must implement')

    def unmarshal_value(self, _from_file):
        check.not_implemented('must implement')
