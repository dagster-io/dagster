from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel


class BespokeELTAssetManifest(BaseModel):
    deps: Optional[List[str]]


class BespokeELTExecutableManifest(BaseModel):
    kind: Literal["bespoke_elt"]
    name: str
    source: str
    destination: str
    assets: Dict[str, BespokeELTAssetManifest]


class DbtExecutableManifest(BaseModel):
    kind: Literal["dbt_manifest"]
    manifest_json_path: str


class HighLevelDSLExecutableList(BaseModel):
    executables: List[Union[BespokeELTExecutableManifest, DbtExecutableManifest]]


class HighLevelDSLManifest(BaseModel):
    group_name: str
    executable_manifest_file: HighLevelDSLExecutableList
