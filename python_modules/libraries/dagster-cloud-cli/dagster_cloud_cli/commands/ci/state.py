import datetime
import json
import os
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Extra, Field

from dagster_cloud_cli.config import models


class DockerBuildOutput(BaseModel, extra=Extra.forbid):
    strategy: Literal["docker"] = "docker"
    python_version: Optional[str] = None
    image: str


class PexBuildOutput(BaseModel, extra=Extra.forbid):
    strategy: Literal["python-executable"] = "python-executable"
    python_version: str
    image: Optional[str]  # if None we determine the image from the python_version and agent version
    pex_tag: str


class BuildMetadata(BaseModel):
    git_url: Optional[str]
    commit_hash: Optional[str]
    build_config: Optional[models.Build]  # copied from dagster_cloud.yaml


class LocationStatus(Enum):
    success = "success"
    pending = "pending"
    failed = "failed"


class StatusChange(BaseModel):
    timestamp: datetime.datetime
    status: LocationStatus
    log: str


class LocationState(BaseModel, extra=Extra.forbid):
    # we intentionally don't save api_token here for security reasons
    url: str
    deployment_name: str
    location_file: str
    location_name: str
    is_branch_deployment: bool
    selected: bool = True
    build: BuildMetadata
    build_output: Optional[Union[DockerBuildOutput, PexBuildOutput]] = Field(
        None, discriminator="strategy"
    )
    status_url: Optional[str]  # link to cicd run url when building and dagster cloud url when done
    history: list[StatusChange] = []

    def add_status_change(self, status: LocationStatus, log: str):
        self.history.append(
            StatusChange(
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                status=status,
                log=log,
            )
        )


class Store(metaclass=ABCMeta):
    @abstractmethod
    def load(self, location_name: str) -> LocationState: ...

    @abstractmethod
    def save(self, location_state: LocationState): ...

    @abstractmethod
    def list_locations(self) -> list[LocationState]: ...

    def list_selected_locations(self) -> list[LocationState]:
        return [location for location in self.list_locations() if location.selected]


class FileStore(Store):
    def __init__(self, statedir: str):
        self.statedir = os.path.abspath(statedir)
        self.location_file_prefix = "location-"
        if not os.path.isdir(self.statedir):
            os.makedirs(self.statedir)

    def __repr__(self):
        return f"<FileStore(statedir={self.statedir!r})>"

    def _get_filepath(self, location_name) -> str:
        return os.path.join(self.statedir, f"{self.location_file_prefix}{location_name}.json")

    def list_locations(self) -> list[LocationState]:
        return [
            self._location_from_file(os.path.join(self.statedir, filename))
            for filename in os.listdir(self.statedir)
            if filename.startswith(self.location_file_prefix)
        ]

    def load(self, location_name: str) -> LocationState:
        filepath = self._get_filepath(location_name)
        if not filepath:
            raise KeyError(f"No saved state for {location_name} at {filepath}")
        return self._location_from_file(self._get_filepath(location_name))

    def _location_from_file(self, filepath: str) -> LocationState:
        with open(filepath, encoding="utf-8") as f:
            return LocationState.parse_obj(json.load(f))

    def save(self, location_state: LocationState):
        filepath = self._get_filepath(location_state.location_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(location_state.json())

    def deselect(self, location_names: list[str]):
        locations = [self.load(location_name) for location_name in location_names]
        for location in locations:
            location.selected = False
            self.save(location)

    def select(self, location_names: list[str]):
        locations = [self.load(location_name) for location_name in location_names]
        for location in locations:
            location.selected = True
            self.save(location)
