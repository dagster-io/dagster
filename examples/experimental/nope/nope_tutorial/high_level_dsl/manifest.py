from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel


class BespokeELTAssetManifest(BaseModel):
    deps: Optional[List[str]]


class BespokeELTInvocationTargetManifest(BaseModel):
    kind: Literal["bespoke_elt"]
    name: str
    source: str
    destination: str
    assets: Dict[str, BespokeELTAssetManifest]


class DbtInvocationTargetManifest(BaseModel):
    kind: Literal["dbt"]
    manifest_json_path: str


class HighLevelDSLGroupFileManifest(BaseModel):
    invocations: List[Union[BespokeELTInvocationTargetManifest, DbtInvocationTargetManifest]]


class HighLevelDSLManifest(BaseModel):
    group_name: str
    manifest_file: HighLevelDSLGroupFileManifest
