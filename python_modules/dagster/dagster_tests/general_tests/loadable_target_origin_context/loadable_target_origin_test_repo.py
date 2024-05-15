from dagster import (
    Definitions,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin

assert LoadableTargetOrigin.get() is not None, "LoadableTargetOrigin is not available from context"

defs = Definitions()
