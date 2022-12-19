from dagster._config.field_utils import config_dictionary_from_values
from dagster._core.definitions.definition_config_schema import (
    ConfiguredDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
from dagster._core.storage.io_manager import IOManagerDefinition


class ConfiguredIOManagerAdapter(IOManagerDefinition):
    def __init__(self, parent_io_manager, args):
        ## TODO: coerce all strings to string source
        super().__init__(
            resource_fn=parent_io_manager.resource_fn,
            config_schema=ConfiguredDefinitionConfigSchema(
                parent_io_manager,
                convert_user_facing_definition_config_schema(
                    None
                ),  # this is actually just replicating a bug that allows for too permissive of config
                config_dictionary_from_values(
                    args,
                    parent_io_manager.config_schema.as_field(),
                ),
            ),
        )
