import json

import requests

from dagster import (
    EventMetadataEntry,
    Field,
    FileHandle,
    Materialization,
    Output,
    String,
    composite_solid,
    solid,
)

from .types import validated_json_type_from_schema_file

# https://github.com/NABSA/gbfs/pull/70
# https://gbfs.baywheels.com/gbfs/gbfs.json


@solid(
    config={
        'from_url': Field(String),
        # Consider an additional requests kwargs config parameter here, perhaps a Permissive
    }
)
def get_json_from_url(context) -> dict:
    context.log.info(str(context.solid_config))
    return requests.get(context.solid_config['from_url']).json()
    # Consider a richer datatype here that lets us set the json schema, etc


def validate_json_solid(validating_json_type, **kwargs):
    @solid(**kwargs)
    def _validate_json_solid(_, obj: dict) -> validating_json_type:
        return validating_json_type(obj)

    return _validate_json_solid


# Probably want this to be a tempdir of some kind
# Actually, do this with s3/gcs/local
@solid
def write_json_to_file(context, obj) -> FileHandle:
    handle = context.file_manager.write_data(bytes(json.dumps(obj), 'utf-8'))
    yield Materialization(
        'materialized_value', metadata_entries=[EventMetadataEntry.text(handle.path, 'json')]
    )
    yield Output(handle)


def download_and_validate_json(schema_file, from_url, **kwargs):

    validating_json_solid = validate_json_solid(validated_json_type_from_schema_file(schema_file))

    @composite_solid(
        config={},
        config_fn=lambda _ctx, _cfg: {'get_json_from_url': {'config': {'from_url': from_url}}},
        **kwargs
    )
    def _download_and_validate_json() -> dict:
        json_value = get_json_from_url()
        validating_json_solid(json_value)
        write_json_to_file(json_value)
        return json_value

    return _download_and_validate_json
