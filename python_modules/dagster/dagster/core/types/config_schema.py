from dagster import check

from .config import resolve_to_config_type


class InputSchema:
    @property
    def schema_cls(self):
        check.not_implemented('Must implement')

    @property
    def schema_type(self):
        return resolve_to_config_type(self.schema_cls)

    def construct_from_config_value(self, value):
        return value


def make_input_schema(dagster_type):
    class _InputSchema(InputSchema):
        @property
        def schema_cls(self):
            return dagster_type

    return _InputSchema()


class OutputSchema:
    @property
    def schema_cls(self):
        check.not_implemented('Must implement')

    @property
    def schema_type(self):
        return resolve_to_config_type(self.schema_cls)

    def materialize_runtime_value(self, _config_value, _runtime_value):
        check.not_implemented('Must implement')
