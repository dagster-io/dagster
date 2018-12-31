from dagster import (
    Field,
    solid,
    types,
)


@solid(config_field=Field(types.Dict({'word': Field(types.String)})))
def double_the_word_with_typed_config(info):
    return info.config['word'] * 2
