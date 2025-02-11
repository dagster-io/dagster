from collections.abc import Mapping
from functools import cached_property
from pathlib import Path

from dotenv import dotenv_values


class Env:
    def __init__(
        self,
        code_location_path: Path,
        deployment_path: Path,
        code_location_values: Mapping[str, str],
        deployment_values: Mapping[str, str],
    ):
        self._code_location_path = code_location_path
        self._deployment_path = deployment_path
        self._code_location_values = dict(code_location_values)
        self._deployment_values = dict(deployment_values)

    @staticmethod
    def from_file(code_location_path: Path, deployment_path: Path) -> "Env":
        code_location_values = {}
        deployment_values = {}
        if code_location_path.exists():
            code_location_values = {
                key: val
                for key, val in dotenv_values(code_location_path).items()
                if val is not None
            }
        if deployment_path.exists():
            deployment_values = {
                key: val for key, val in dotenv_values(deployment_path).items() if val is not None
            }
        return Env(code_location_path, deployment_path, code_location_values, deployment_values)

    def __getitem__(self, key: str) -> str:
        return self._code_location_values.get(key) or self._deployment_values[key]

    @cached_property
    def values(self) -> Mapping[str, str]:
        return {**self._deployment_values, **self._code_location_values}

    @property
    def code_location_values(self) -> Mapping[str, str]:
        return self._code_location_values

    @property
    def deployment_values(self) -> Mapping[str, str]:
        return self._deployment_values

    def unset_code_location_value(self, key: str) -> None:
        del self._code_location_values[key]
        self._write()

    def unset_deployment_value(self, key: str) -> None:
        del self._deployment_values[key]
        self._write()

    def set_code_location_value(self, key: str, value: str) -> None:
        self._code_location_values[key] = value
        self._write()

    def set_deployment_value(self, key: str, value: str) -> None:
        self._deployment_values[key] = value
        self._write()

    def _write(self) -> None:
        if self._code_location_values or self._code_location_path.exists():
            self._code_location_path.write_text(
                "\n".join(f"{key}={value}" for key, value in self._code_location_values.items())
            )
        if self._deployment_path.exists() or self._deployment_values:
            self._deployment_path.write_text(
                "\n".join(f"{key}={value}" for key, value in self._deployment_values.items())
            )
