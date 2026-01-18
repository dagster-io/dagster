from typing import Any, Optional, Union

from pydantic import BaseModel


class ConcurrencyPools(BaseModel, extra="forbid"):
    defaultLimit: Optional[int] = None
    granularity: Optional[str] = None  # "run" or "op"
    opGranularityRunBuffer: Optional[int] = None


class TagConcurrencyLimit(BaseModel, extra="forbid"):
    key: str
    value: Optional[Union[str, dict[str, Any]]] = None
    limit: int


class ConcurrencyRuns(BaseModel, extra="forbid"):
    maxConcurrentRuns: Optional[int] = None
    tagConcurrencyLimits: list[TagConcurrencyLimit] = []


class Concurrency(BaseModel, extra="forbid"):
    enabled: bool = False
    pools: ConcurrencyPools = ConcurrencyPools()
    runs: ConcurrencyRuns = ConcurrencyRuns()
