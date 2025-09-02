"""Asset models for REST-like API."""

from typing import Optional

from pydantic import BaseModel


class DgApiAsset(BaseModel):
    """Asset resource model."""

    id: str
    asset_key: str  # "my/asset/key"
    asset_key_parts: list[str]  # ["my", "asset", "key"]
    description: Optional[str]
    group_name: str
    kinds: list[str]
    tags: Optional[list[dict]] = []
    metadata_entries: list[dict]

    class Config:
        from_attributes = True


class DgApiAssetList(BaseModel):
    """GET /api/assets response."""

    items: list[DgApiAsset]
    cursor: Optional[str]  # Next cursor for pagination
    has_more: bool  # Whether more results exist
