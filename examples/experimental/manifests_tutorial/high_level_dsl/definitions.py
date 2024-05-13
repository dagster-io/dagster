from pathlib import Path
from typing import List, Type

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._manifest.definitions import (
    ManifestBackedExecutableFactory,
)
from dagster._manifest.executable import ManifestBackedExecutable
from dagster._manifest.executables.subprocess import (
    PipesSubprocessManifestExecutable,
)
from dagster_dbt.core.resources_v2 import DbtCliResource
from executables.bespoke_elt import BespokeELTExecutable
from executables.dbt_manifest import DbtManifestJsonExecutable
from manifest import HighLevelDSLManifest
from manifest_source import HighLevelDSLFileSystemManifestSource


class HighLevelDSLManifestFactory(ManifestBackedExecutableFactory[HighLevelDSLManifest]):
    @classmethod
    def executables(cls) -> List[Type[ManifestBackedExecutable]]:
        return [
            BespokeELTExecutable,
            DbtManifestJsonExecutable,
            PipesSubprocessManifestExecutable,
        ]


def dbt_project_dir() -> str:
    return str((Path(__file__).parent / Path("jaffle_shop")).resolve())


def manifests_path() -> Path:
    return Path(__file__).resolve().parent / Path("manifests")


def create_manifest() -> HighLevelDSLManifest:
    return HighLevelDSLFileSystemManifestSource(path=manifests_path()).get_manifest()


def make_high_level_dsl_definitions() -> Definitions:
    return HighLevelDSLManifestFactory().make_definitions(
        manifest=create_manifest(),
        resources={
            "dbt": DbtCliResource(dbt_project_dir()),
            "subprocess_client": PipesSubprocessClient(),
        },
    )


defs = make_high_level_dsl_definitions()

if __name__ == "__main__":
    assert isinstance(defs, Definitions)
