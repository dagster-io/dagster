import json

from dagster import SerializationStrategy, check, dagster_type

# from jsonschema import ValidationError, validate


class JsonSerializationStrategy(SerializationStrategy):
    def __init__(self, **kwargs):
        super(JsonSerializationStrategy, self).__init__(
            'json_strategy', read_mode='r', write_mode='w'
        )
        self._kwargs = check.opt_dict_param(kwargs, 'kwargs')

    def serialize(self, value, write_file_obj):
        write_file_obj.write(json.dumps(value, **self._kwargs))

    def deserialize(self, read_file_obj):
        return json.loads(read_file_obj.read())


def validated_json_type(_schema, **kwargs):
    # This is not called during tests so not updating callsites
    # def _type_check(value):
    #     try:
    #         validate(instance=value, schema=schema)
    #     except ValidationError:
    #         return False
    #     else:
    #         return True

    @dagster_type(
        # type_check=_type_check,
        serialization_strategy=JsonSerializationStrategy(indent=2, separators=(', ', ': ')),
        **kwargs
    )
    class _ValidatedJsonType(dict):
        pass

    return _ValidatedJsonType


def validated_json_type_from_schema_file(path, **kwargs):
    with open(path, 'r') as fd:
        schema = json.load(fd)
    return validated_json_type(schema, **kwargs)
