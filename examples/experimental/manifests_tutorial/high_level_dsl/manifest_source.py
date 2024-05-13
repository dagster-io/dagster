from pathlib import Path
from typing import Iterable

from dagster import _check as check
from dagster._manifest.definitions import (
    ManifestSource,
)
from dagster._manifest.pydantic_yaml import load_yaml_to_pydantic
from manifest import (
    HighLevelDSLManifest,
)


class HighLevelDSLFileSystemManifestSource(ManifestSource):
    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def get_yaml_files(path: Path) -> Iterable[Path]:
        for file_path in path.iterdir():
            if file_path.suffix == ".yaml":
                yield file_path

    def get_manifest(self) -> "HighLevelDSLManifest":
        all_executables = []
        manifests_by_default_group = {}
        for yaml_file in self.get_yaml_files(self.path):
            manifests_by_default_group[yaml_file.stem] = check.inst(
                load_yaml_to_pydantic(str(yaml_file), HighLevelDSLManifest),
                HighLevelDSLManifest,
            ).executables

        for group_name, executables in manifests_by_default_group.items():
            for executable in executables:
                if executable.group_name is None:
                    all_executables.append(executable.copy(update={"group_name": group_name}))
                else:
                    all_executables.append(executable)

        return HighLevelDSLManifest(executables=all_executables)
