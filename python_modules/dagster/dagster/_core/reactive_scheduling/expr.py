from abc import abstractmethod
from typing import Callable

from dagster._core.reactive_scheduling.asset_graph_view import AssetSlice
from dagster._core.reactive_scheduling.scheduling_policy import SchedulingExecutionContext

from .scheduling_plan import RulesLogic


class Expr:
    @staticmethod
    def latest_time_window() -> "ExprNode":
        return LeafExpr(RulesLogic.latest_time_window)

    @staticmethod
    def any_parent_updated() -> "ExprNode":
        return LeafExpr(RulesLogic.any_parent_updated)

    @staticmethod
    def unsynced() -> "ExprNode":
        return LeafExpr(RulesLogic.unsynced)


class ExprNode:
    @abstractmethod
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        ...

    def __and__(self, other: "ExprNode") -> "ExprNode":
        return AndExpr(self, other)


class AndExpr(ExprNode):
    def __init__(self, left: ExprNode, right: ExprNode):
        self.left = left
        self.right = right

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        left_slice = self.left.evaluate(context, current_slice)
        right_slice = self.right.evaluate(context, current_slice)
        result_slice = left_slice.intersection(right_slice)
        return result_slice


class LeafExpr(ExprNode):
    def __init__(self, callabe: Callable):
        self.callable = callabe

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        return self.callable(context, current_slice)
