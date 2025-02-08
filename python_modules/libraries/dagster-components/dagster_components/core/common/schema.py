from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

from pydantic import BaseModel

from dagster_components.core.schema.base import ComponentSchema


class OpSpecSchema(ComponentSchema):
    name: Optional[str] = None
    tags: Optional[dict[str, str]] = None


class AssetDepSchema(ComponentSchema):
    asset: str
    partition_mapping: Optional[str] = None


class _ResolvableAssetAttributesMixin(BaseModel):
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Union[str, Mapping[str, Any]] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Union[str, Mapping[str, str]] = {}
    kinds: Optional[Sequence[str]] = None
    automation_condition: Optional[str] = None


class AssetAttributesSchema(_ResolvableAssetAttributesMixin, ComponentSchema):
    key: Optional[str] = None


class AssetSpecSchema(_ResolvableAssetAttributesMixin, ComponentSchema):
    key: str
