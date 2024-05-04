import yaml
from pydantic import BaseModel, ValidationError


def load_yaml(path: str) -> dict:
    with open(path, "r") as file:
        return yaml.safe_load(file)


def load_yaml_to_pydantic(yaml_path: str, pydantic_class) -> BaseModel:
    """Reads a YAML file, ensures its schema is compatible with a given Pydantic class,
    and returns an instance of that Pydantic class.

    :param yaml_path: The path to the YAML file to be loaded.
    :param pydantic_class: The Pydantic class to validate against.
    :return: An instance of the Pydantic class with the loaded data.
    :raises ValueError: If the YAML data does not match the schema.
    """
    data = load_yaml(yaml_path)
    try:
        instance = pydantic_class(**data)
        return instance

    except (yaml.YAMLError, ValidationError) as error:
        raise ValueError(f"Failed to parse YAML or validate schema: {error}")
