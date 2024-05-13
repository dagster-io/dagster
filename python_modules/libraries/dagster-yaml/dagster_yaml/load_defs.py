from pathlib import Path

from dagster import Definitions

from dagster_yaml.definition_set_config import DefinitionSetConfig
from dagster_yaml.yaml.pydantic_yaml import parse_yaml_file


def load_defs_from_yaml(path: str, config_type: type[DefinitionSetConfig]) -> Definitions:
    """Load Dagster definitions from a YAML file.

    This function is responsible for parsing the YAML file, creating the Dagster Definitions
    object, and populating the object mapping context for the parsed YAML data.

    Args:
        path (str): The path to the YAML file or directory of YAML files containing the Dagster
            definitions.
        config_type (type[DefinitionSetConfig]): The type of definition config that each of the YAML
            files are expected to conform to.

    Returns:
        Definitions: The loaded Dagster Definitions object.
    """
    resolved_path = Path(path)
    file_paths: list[Path]
    if resolved_path.is_file():
        file_paths = [resolved_path]
    else:
        file_paths = list(resolved_path.rglob("*.yaml")) + list(resolved_path.rglob("*.yml"))

    def_set_configs = [
        parse_yaml_file(config_type, file_path.read_text(), str(file_path))
        for file_path in file_paths
    ]

    def_sets = [
        def_set_config.build_defs_add_context_to_errors() for def_set_config in def_set_configs
    ]

    return Definitions.merge(*def_sets)
