from typing import Dict, List, Optional

from pydantic import BaseModel


class BespokeELTAssetManifest(BaseModel):
    deps: Optional[List[str]]


class BespokeELTInvocationTargetManifest(BaseModel):
    name: str
    target: str
    source: str
    destination: str
    assets: Dict[str, BespokeELTAssetManifest]


class HighLevelDSLGroupFileManifest(BaseModel):
    invocations: List[BespokeELTInvocationTargetManifest]


class HighLevelDSLManifest(BaseModel):
    group_name: str
    manifest_file: HighLevelDSLGroupFileManifest
