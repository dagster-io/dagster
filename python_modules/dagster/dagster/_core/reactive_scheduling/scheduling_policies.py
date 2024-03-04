from dagster._core.reactive_scheduling.expr import Expr
from dagster._core.reactive_scheduling.scheduling_policy import SchedulingPolicy


class DefaultSchedulingPolicy(SchedulingPolicy):
    def __init__(self) -> None:
        super().__init__(
            # TODO: support or
            # expr=Expr.latest_complete_time_window() & (Expr.unsynced() | Expr.any_parent_updated())
            expr=Expr.latest_complete_time_window() & (Expr.unsynced())
        )
