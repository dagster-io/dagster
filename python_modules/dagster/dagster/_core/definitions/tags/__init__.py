from typing import Any, Dict, Mapping

from dagster._core.definitions.tags.tag_set import NamespacedTagSet as NamespacedTagSet
from dagster._core.storage.tags import KIND_PREFIX


def has_kind(tags: Mapping[str, Any], kind: str) -> bool:
    return build_kind_tag_key(kind) in tags


def build_kind_tag_key(kind: str) -> str:
    return f"{KIND_PREFIX}{kind}"


def build_kind_tag(kind: str) -> Dict[str, Any]:
    return {build_kind_tag_key(kind): ""}
