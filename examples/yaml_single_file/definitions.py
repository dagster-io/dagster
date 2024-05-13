from dagster import Definitions, PipesSubprocessClient
from dagster_yaml import load_defs_from_yaml
from dagster_yaml.multi_definition_set_config import MultiDefinitionSetConfig
from dagster_yaml.shell.shell_asset_definition_config import ShellAssetDefinitionConfig

defs = Definitions.merge(
    load_defs_from_yaml(".", config_type=MultiDefinitionSetConfig[ShellAssetDefinitionConfig]),
    Definitions(resources={"subprocess_client": PipesSubprocessClient()}),
)
