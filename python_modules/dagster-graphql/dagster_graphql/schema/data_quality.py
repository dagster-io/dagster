import json

import graphene
from dagster import AssetCheckKey
from dagster._core.definitions.data_quality import DataQualityConfig
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecord
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster_shared import seven
from graphene.types.generic import GenericScalar

from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneDataQualityCheckExecution(graphene.ObjectType):
    checkExecution = graphene.NonNull(GrapheneAssetCheckExecution)
    logsForExecution = graphene.Field(
        graphene.NonNull("dagster_graphql.schema.instigation.GrapheneInstigationEventConnection"),
        cursor=graphene.String(),
    )

    def __init__(self, check_execution: AssetCheckExecutionRecord):
        self._execution_id = check_execution.run_id
        self._check_name = check_execution.key.name
        super().__init__(
            checkExecution=GrapheneAssetCheckExecution(check_execution),
        )

    def resolve_logsForExecution(self, graphene_info: ResolveInfo, cursor: str):
        from dagster_graphql.schema.instigation import (
            GrapheneInstigationEvent,
            GrapheneInstigationEventConnection,
        )
        from dagster_graphql.schema.logs.log_level import GrapheneLogLevel

        if self._execution_id is None:
            return GrapheneInstigationEventConnection(
                events=[],
                cursor=cursor,
                hasMore=False,
            )

        asset_check_log_key_prefix = [self._execution_id, self._check_name]

        instance = graphene_info.context.instance

        records, new_cursor = instance.compute_log_manager.read_log_lines_for_log_key_prefix(
            asset_check_log_key_prefix, cursor=cursor, io_type=ComputeIOType.STDERR
        )

        events = []
        for line in records:
            if not line:
                continue
            try:
                record_dict = seven.json.loads(line)
            except json.JSONDecodeError:
                continue

            exc_info = record_dict.get("exc_info")
            message = record_dict.get("msg")
            if exc_info:
                message = f"{message}\n\n{exc_info}"
            event = GrapheneInstigationEvent(
                message=message,
                level=GrapheneLogLevel.from_level(record_dict["levelno"]),
                timestamp=int(record_dict["created"] * 1000),
            )

            events.append(event)

        return GrapheneInstigationEventConnection(
            events=events,
            cursor=new_cursor.to_string() if new_cursor else "",
            hasMore=new_cursor.has_more_now if new_cursor else False,
        )


class GrapheneDataQualityCheck(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)
    description = graphene.String()
    config = graphene.NonNull(GenericScalar)
    instigator = graphene.NonNull(graphene.String)
    checkType = graphene.NonNull(graphene.String)  # TODO - make enum

    executionHistory = graphene.Field(
        non_null_list(GrapheneDataQualityCheckExecution),
        limit=graphene.Int(),
    )

    class Meta:
        name = "DataQualityCheck"

    def __init__(self, check_config: DataQualityConfig):
        self._check_config = check_config
        super().__init__(
            name=check_config.name,
            assetKey=check_config.asset_key,
            description=check_config.description,
            config=check_config.config,
            instigator=check_config.instigator,
            checkType=check_config.check_type,
        )

    def resolve_executionHistory(self, graphene_info: ResolveInfo, limit: int):
        check_key = AssetCheckKey(name=self.name, asset_key=self.assetKey)
        records = (
            graphene_info.context.instance.event_log_storage.get_asset_check_execution_history(
                check_key=check_key,
                limit=limit,
                cursor=None,  # TODO - cursor
            )
        )

        return [GrapheneDataQualityCheckExecution(record) for record in records]
