from typing import Any, Mapping, NamedTuple, Optional


class AssetIn(NamedTuple):
    metadata: Optional[Mapping[str, Any]] = None
    namespace: Optional[str] = None
    managed: bool = True
