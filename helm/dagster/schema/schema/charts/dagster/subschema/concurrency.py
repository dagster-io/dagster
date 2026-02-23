from typing import Any

from pydantic import BaseModel


class ConcurrencyPools(BaseModel, extra="forbid"):
    defaultLimit: int | None = None
    granularity: str | None = None  # "run" or "op"
    opGranularityRunBuffer: int | None = None


class TagConcurrencyLimit(BaseModel, extra="forbid"):
    key: str
    value: str | dict[str, Any] | None = None
    limit: int


class ConcurrencyRuns(BaseModel, extra="forbid"):
    maxConcurrentRuns: int | None = None
    tagConcurrencyLimits: list[TagConcurrencyLimit] = []


class Concurrency(BaseModel, extra="forbid"):
    enabled: bool = False
    pools: ConcurrencyPools = ConcurrencyPools()
    runs: ConcurrencyRuns = ConcurrencyRuns()
