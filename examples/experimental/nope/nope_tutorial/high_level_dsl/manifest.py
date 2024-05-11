from typing import List, Union

from bespoke_elt import BespokeELTExecutableManifest
from dbt_executable import DbtExecutableManifest
from pydantic import BaseModel


class HighLevelDSLExecutableList(BaseModel):
    executables: List[Union[BespokeELTExecutableManifest, DbtExecutableManifest]]


class HighLevelDSLManifest(BaseModel):
    group_name: str
    executable_manifest_file: HighLevelDSLExecutableList
