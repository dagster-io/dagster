from pathlib import Path

from dagster import _check as check
from dagster._nope.definitions import (
    ManifestSource,
)
from dagster._nope.parser import load_yaml_to_pydantic
from manifest import (
    HighLevelDSLGroupFileManifest,
    HighLevelDSLManifest,
)


class HighLevelDSLFileSystemManifestSource(ManifestSource):
    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def _get_single_yaml_file(path: Path) -> Path:
        yaml_files = {}
        for file_path in path.iterdir():
            # python_files = {}
            if file_path.suffix == ".yaml":
                yaml_files[file_path.stem] = file_path

        if len(yaml_files) != 1:
            raise Exception(f"Expected exactly one yaml file in {path}, found {yaml_files}")
        return next(iter(yaml_files.values()))

    def get_manifest(self) -> HighLevelDSLManifest:
        single_group_yaml_file = HighLevelDSLFileSystemManifestSource._get_single_yaml_file(
            self.path
        )
        group_file_manifest = check.inst(
            load_yaml_to_pydantic(str(single_group_yaml_file), HighLevelDSLGroupFileManifest),
            HighLevelDSLGroupFileManifest,
        )
        return HighLevelDSLManifest(group_name=self.path.stem, manifest_file=group_file_manifest)
