from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiInstigationTickStatus
from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiTickError(BaseModel):
    message: str
    stack: list[str] | None = None

    class Config:
        from_attributes = True


class DgApiTick(BaseModel):
    id: str
    status: DgApiInstigationTickStatus
    timestamp: float
    end_timestamp: float | None = None
    run_ids: list[str]
    error: DgApiTickError | None = None
    skip_reason: str | None = None
    cursor: str | None = None

    class Config:
        from_attributes = True


# TODO: switch this to a paginated list and add support for user pagination in the cli
# can derive has_more by querying for limit + 1 items, has_more = limit + 1 items returned
# then slice the result to items[:limit] to show the user
# right now total is a lie (always just shows the number returned)
# and the formatter does not expose the cursor or the hasMore so users can manually get the next page
class DgApiTickList(DgApiTruncatedList[DgApiTick]):
    cursor: str | None = None
