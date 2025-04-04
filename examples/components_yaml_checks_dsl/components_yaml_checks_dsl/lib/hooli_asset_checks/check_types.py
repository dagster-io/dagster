from typing import Literal, Optional

from dagster.components import Model
from typing_extensions import TypeAlias


class StaticThresholdCheck(Model):
    type: Literal["static_threshold"]
    asset: str
    check_name: str
    metric: str
    min: Optional[int] = None
    max: Optional[int] = None


HooliAssetCheck: TypeAlias = StaticThresholdCheck
HooliAssetCheckType: TypeAlias = Literal["static_threshold"]
