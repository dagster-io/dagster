from dagster import check
from dagster.config.field_utils import Permissive

from .config_schema import input_hydration_config
from .dagster_type import DagsterType, PythonObjectDagsterType, resolve_dagster_type


@input_hydration_config(Permissive())
def _dict_input(_context, value):
    return value


PythonDict = PythonObjectDagsterType(
    dict,
    'PythonDict',
    input_hydration_config=_dict_input,
    description='''Represents a python dictionary to pass between solids''',
)


class _TypedPythonDict(DagsterType):
    def __init__(self, key_type, value_type):
        self.key_type = check.inst_param(key_type, 'key_type', DagsterType)
        self.value_type = check.inst_param(value_type, 'value_type', DagsterType)
        super(_TypedPythonDict, self).__init__(
            key='TypedPythonDict.{}.{}'.format(key_type.key, value_type.key),
            name=None,
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, context, value):
        from dagster.core.definitions.events import TypeCheck

        if not isinstance(value, dict):
            return TypeCheck(
                success=False,
                description='Value should be a dict, got a {value_type}'.format(
                    value_type=type(value)
                ),
            )

        for key, value in value.items():
            key_check = self.key_type.type_check(context, key)
            if not key_check.success:
                return key_check
            value_check = self.value_type.type_check(context, value)
            if not value_check.success:
                return value_check

        return TypeCheck(success=True)

    @property
    def display_name(self):
        return 'Dict[{key},{value}]'.format(
            key=self.key_type.display_name, value=self.value_type.display_name
        )

    @property
    def inner_types(self):
        return [self.key_type, self.value_type]

    @property
    def type_param_keys(self):
        return [self.key_type.key, self.value_type.key]


def create_typed_runtime_dict(key_dagster_type, value_dagster_type):
    key_type = resolve_dagster_type(key_dagster_type)
    value_type = resolve_dagster_type(value_dagster_type)

    return _TypedPythonDict(key_type, value_type)


class DagsterDictApi(object):
    def __getitem__(self, *args):
        check.param_invariant(len(args[0]) == 2, 'args', 'Must be two parameters')
        return create_typed_runtime_dict(args[0][0], args[0][1])


Dict = DagsterDictApi()
