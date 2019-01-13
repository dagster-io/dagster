import json

from dagster import check

from .config import ConfigTypeAttributes, Dict, NamedSelector, Path, Int, String, Bool, Any
from .config_schema import OutputSchema, make_input_schema
from .field_utils import FieldImpl


def define_path_dict_field():
    return FieldImpl(Dict({'path': FieldImpl(Path.inst())}).inst())


def define_builtin_scalar_output_schema(scalar_name):
    check.str_param(scalar_name, 'scalar_name')

    schema_cls = NamedSelector(
        scalar_name + '.MaterializationSchema',
        {'json': define_path_dict_field()},
        type_attributes=ConfigTypeAttributes(is_system_config=True),
    )

    class _BuiltinScalarOutputSchema(OutputSchema):
        @property
        def schema_cls(self):
            return schema_cls

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

    return _BuiltinScalarOutputSchema()


class BuiltinSchemas:
    INT_INPUT = make_input_schema(Int)
    INT_OUTPUT = define_builtin_scalar_output_schema('Int')

    STRING_INPUT = make_input_schema(String)
    STRING_OUTPUT = define_builtin_scalar_output_schema('String')

    PATH_INPUT = make_input_schema(Path)
    PATH_OUTPUT = define_builtin_scalar_output_schema('Path')

    BOOL_INPUT = make_input_schema(Bool)
    BOOL_OUTPUT = define_builtin_scalar_output_schema('Bool')

    ANY_INPUT = make_input_schema(Any)
    ANY_OUTPUT = define_builtin_scalar_output_schema('Any')
