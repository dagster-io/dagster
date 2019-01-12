from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check

from .config import resolve_to_config_type


@six.add_metaclass(ABCMeta)
class InputSchema:
    @abstractproperty
    def schema_cls(self):
        pass

    @property
    def schema_type(self):
        return resolve_to_config_type(self.schema_cls)

    def construct_from_config_value(self, value):
        return value


@six.add_metaclass(ABCMeta)
class SelectorInputSchema(InputSchema):
    def __init__(self, *args, **kwargs):
        super(SelectorInputSchema, self).__init__(*args, **kwargs)

        if not self.schema_type.is_selector:
            raise Exception('nope')

    def construct_from_config_value(self, value):
        check.dict_param(value, 'value', key_type=str)
        check.param_invariant(len(value) == 1, 'value')

        selector_key, selector_value = list(value.items())[0]
        return self.construct_from_selector_value(selector_key, selector_value)

    @abstractmethod
    def construct_from_selector_value(self, selector_key, selector_value):
        pass


class _GenericInputSchema(InputSchema):
    def __init__(self, dagster_type):
        self.dagster_type = dagster_type

    @property
    def schema_cls(self):
        return self.dagster_type


def make_input_schema(dagster_type):
    return _GenericInputSchema(dagster_type)


@six.add_metaclass(ABCMeta)
class OutputSchema:
    @abstractproperty
    def schema_cls(self):
        pass

    @property
    def schema_type(self):
        return resolve_to_config_type(self.schema_cls)

    def materialize_runtime_value(self, _config_value, _runtime_value):
        check.not_implemented('Must implement')


@six.add_metaclass(ABCMeta)
class SelectorOutputSchema(OutputSchema):
    def __init__(self, *args, **kwargs):
        super(SelectorOutputSchema, self).__init__(*args, **kwargs)

        if not self.schema_type.is_selector:
            raise Exception('nope')

    def materialize_runtime_value(self, config_value, runtime_value):
        check.dict_param(config_value, 'config_value', key_type=str)
        check.param_invariant(len(config_value) == 1, 'config_value')

        selector_key, selector_value = list(config_value.items())[0]
        return self.materialize_selector_runtime_value(selector_key, selector_value, runtime_value)

    @abstractmethod
    def materialize_selector_runtime_value(self, selector_key, selector_value, runtime_value):
        pass
