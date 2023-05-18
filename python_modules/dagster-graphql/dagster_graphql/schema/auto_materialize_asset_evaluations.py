from typing import cast

import dagster._check as check
import graphene
from dagster._core.definitions.auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    DownstreamFreshnessAutoMaterializeCondition,
    FreshnessAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from .util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GrapheneAutoMaterializeConditionWithDecisionType(graphene.Interface):
    decisionType = graphene.NonNull(GrapheneAutoMaterializeDecisionType)

    class Meta:
        name = "AutoMaterializeConditionWithDecisionType"


class GrapheneFreshnessAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "FreshnessAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneDownstreamFreshnessAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "DownstreamFreshnessAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneParentMaterializedAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "ParentMaterializedAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneMissingAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "MissingAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneParentOutdatedAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "ParentOutdatedAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneAutoMaterializeCondition(graphene.Union):
    class Meta:
        name = "AutoMaterializeCondition"
        types = (
            GrapheneFreshnessAutoMaterializeCondition,
            GrapheneDownstreamFreshnessAutoMaterializeCondition,
            GrapheneParentMaterializedAutoMaterializeCondition,
            GrapheneMissingAutoMaterializeCondition,
            GrapheneParentOutdatedAutoMaterializeCondition,
        )


def create_graphene_auto_materialize_condition(condition: AutoMaterializeCondition):
    if isinstance(condition, FreshnessAutoMaterializeCondition):
        return GrapheneFreshnessAutoMaterializeCondition(decisionType=condition.decision_type)
    elif isinstance(condition, DownstreamFreshnessAutoMaterializeCondition):
        return GrapheneDownstreamFreshnessAutoMaterializeCondition(
            decisionType=condition.decision_type
        )
    elif isinstance(condition, ParentMaterializedAutoMaterializeCondition):
        return GrapheneParentMaterializedAutoMaterializeCondition(
            decisionType=condition.decision_type
        )
    elif isinstance(condition, MissingAutoMaterializeCondition):
        return GrapheneMissingAutoMaterializeCondition(decisionType=condition.decision_type)
    elif isinstance(condition, ParentOutdatedAutoMaterializeCondition):
        return GrapheneParentOutdatedAutoMaterializeCondition(decisionType=condition.decision_type)
    else:
        check.failed(f"Unexpected condition type {type(condition)}")


class GrapheneAutoMaterializeAssetEvaluationRecord(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    evaluationId = graphene.NonNull(graphene.Int)
    numRequested = graphene.NonNull(graphene.Int)
    numSkipped = graphene.NonNull(graphene.Int)
    numDiscarded = graphene.NonNull(graphene.Int)
    conditions = non_null_list(GrapheneAutoMaterializeCondition)

    class Meta:
        name = "AutoMaterializeAssetEvaluationRecord"

    def __init__(self, record: AutoMaterializeAssetEvaluationRecord):
        conditions = [
            # NOTE: Hacky check for if this is partitioned or not! Python doesn't support isinstance with Unions,
            # so instead we check against __args__ which is the list of types that the Union is composed of
            cast(AutoMaterializeCondition, i if isinstance(i, AutoMaterializeCondition.__args__) else i[0])  # type: ignore
            for i in record.evaluation.conditions
        ]
        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            numRequested=record.evaluation.num_requested,
            numSkipped=record.evaluation.num_skipped,
            numDiscarded=record.evaluation.num_discarded,
            conditions=[create_graphene_auto_materialize_condition(c) for c in conditions],
        )
