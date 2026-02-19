"""Use a pydantic definition to validate dagster_cloud.yaml."""

from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class CodeSource(BaseModel, extra="forbid"):
    package_name: str | None = None
    module_name: str | None = None
    python_file: str | None = None
    autoload_defs_module_name: str | None = None

    @model_validator(mode="before")
    def exactly_one_source_defined(cls, values: dict[str, str | None]) -> dict[str, str | None]:
        defined = [key for key, value in values.items() if value]
        if len(defined) > 1:
            raise ValueError(
                "only one of the following fields should be defined: " + ", ".join(defined)
            )
        elif not defined:
            raise ValueError(
                "one of package_name, module_name, python_file, or autoload_defs_module_name must be specified"
            )
        return values


class Build(BaseModel, extra="forbid"):
    directory: str | None = None
    registry: str | None = None


class Location(BaseModel, extra="forbid"):
    location_name: str
    code_source: CodeSource | None = None
    build: Build | None = None
    working_directory: str | None = None
    image: str | None = None
    executable_path: str | None = None
    attribute: str | None = None
    container_context: dict[str, Any] | None = None
    agent_queue: str | None = None


class LocationDefaults(BaseModel, extra="forbid"):
    build: Build | None = None
    working_directory: str | None = None
    image: str | None = None
    executable_path: str | None = None
    container_context: dict[str, Any] | None = None
    agent_queue: str | None = None


class DagsterCloudYaml(BaseModel, extra="forbid"):
    defaults: LocationDefaults | None = Field(
        description="Default values for code locations", default=None
    )
    locations: list[Location] = Field(description="List of code locations")

    @field_validator("locations")
    def no_duplicate_names(cls, v: list[Location]) -> list[Location]:
        names = set()
        for location in v:
            if location.location_name in names:
                raise ValueError(f"duplicate location name: {location.location_name}")
            names.add(location.location_name)
        return v


class ProcessedDagsterCloudConfig(BaseModel, extra="forbid"):
    locations: list[Location] = Field(description="List of code locations")


def load_dagster_cloud_yaml(text) -> DagsterCloudYaml:
    return DagsterCloudYaml.model_validate(yaml.safe_load(text))
