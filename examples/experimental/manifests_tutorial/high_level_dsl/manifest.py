from typing import List, Union

from dagster._manifest.executables.subprocess import SubprocessExecutableManifest
from executables.bespoke_elt import BespokeELTExecutableManifest
from executables.dbt_manifest import DbtManifestJsonExecutableManifest
from pydantic import BaseModel


class HighLevelDSLManifest(BaseModel):
    executables: List[
        Union[
            BespokeELTExecutableManifest,
            DbtManifestJsonExecutableManifest,
            SubprocessExecutableManifest,
        ]
    ]
