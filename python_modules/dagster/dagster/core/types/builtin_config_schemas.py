import json
import pickle

from dagster import check, seven

from .config import ConfigTypeAttributes, Path, Int, String, Bool, Any, Float
from .config_schema import make_bare_input_schema, input_selector_schema, output_selector_schema
from .field_utils import FieldImpl, Dict, NamedSelector


def define_builtin_scalar_input_schema(scalar_name, config_scalar_type):
    check.str_param(scalar_name, 'scalar_name')

    @input_selector_schema(
        NamedSelector(
            scalar_name + '.InputHydrationConfig',
            {
                'value': FieldImpl(config_scalar_type),
                'json': define_path_dict_field(),
                'pickle': define_path_dict_field(),
            },
            type_attributes=ConfigTypeAttributes(is_system_config=True),
        )
    )
    def _builtin_input_schema(_context, file_type, file_options):
        if file_type == 'value':
            return file_options
        elif file_type == 'json':
            with open(file_options['path'], 'r') as ff:
                value_dict = json.load(ff)
                return value_dict['value']
        elif file_type == 'pickle':
            with open(file_options['path'], 'rb') as ff:
                return pickle.load(ff)
        else:
            check.failed('Unsupported key {key}'.format(key=file_type))

    return _builtin_input_schema


def define_path_dict_field():
    return FieldImpl(Dict({'path': FieldImpl(Path.inst())}).inst())


def define_builtin_scalar_output_schema(scalar_name):
    check.str_param(scalar_name, 'scalar_name')

    schema_cls = NamedSelector(
        scalar_name + '.MaterializationSchema',
        {'json': define_path_dict_field(), 'pickle': define_path_dict_field()},
        type_attributes=ConfigTypeAttributes(is_system_config=True),
    )

    @output_selector_schema(schema_cls)
    def _builtin_output_schema(_context, file_type, file_options, runtime_value):
        from dagster.core.events import Materialization

        if file_type == 'json':
            json_file_path = file_options['path']
            json_value = seven.json.dumps({'value': runtime_value})
            with open(json_file_path, 'w') as ff:
                ff.write(json_value)
            return Materialization.file(json_file_path)
        elif file_type == 'pickle':
            pickle_file_path = file_options['path']
            with open(pickle_file_path, 'wb') as ff:
                pickle.dump(runtime_value, ff)
            return Materialization.file(pickle_file_path)
        else:
            check.failed('Unsupported file type: {file_type}'.format(file_type=file_type))

    return _builtin_output_schema


class BuiltinSchemas:
    ANY_INPUT = define_builtin_scalar_input_schema('Any', Any.inst())
    ANY_OUTPUT = define_builtin_scalar_output_schema('Any')

    BOOL_INPUT = define_builtin_scalar_input_schema('Bool', Bool.inst())
    BOOL_OUTPUT = define_builtin_scalar_output_schema('Bool')

    FLOAT_INPUT = define_builtin_scalar_input_schema('Float', Float.inst())
    FLOAT_OUTPUT = define_builtin_scalar_output_schema('Float')

    INT_INPUT = define_builtin_scalar_input_schema('Int', Int.inst())
    INT_OUTPUT = define_builtin_scalar_output_schema('Int')

    PATH_INPUT = make_bare_input_schema(Path)
    PATH_OUTPUT = define_builtin_scalar_output_schema('Path')

    STRING_INPUT = define_builtin_scalar_input_schema('String', String.inst())
    STRING_OUTPUT = define_builtin_scalar_output_schema('String')
