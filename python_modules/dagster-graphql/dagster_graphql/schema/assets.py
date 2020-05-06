from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_assets import get_asset_events
from dagster_graphql.implementation.fetch_runs import get_run_by_id
from dagster_graphql.schema.runs import construct_basic_params

from dagster import check
from dagster.core.events.log import EventRecord

from .errors import DauphinError


class DauphinAsset(dauphin.ObjectType):
    class Meta(object):
        name = 'Asset'

    key = dauphin.NonNull(dauphin.String)
    assetMaterializations = dauphin.Field(
        dauphin.non_null_list('AssetMaterialization'), cursor=dauphin.String(), limit=dauphin.Int(),
    )

    def resolve_assetMaterializations(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named('AssetMaterialization')(event=event)
            for event in get_asset_events(
                graphene_info, self.key, kwargs.get('cursor'), kwargs.get('limit')
            )
        ]


class DauphinAssetMaterialization(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetMaterialization'

    def __init__(self, event):
        self._event = check.inst_param(event, 'event', EventRecord)

    materializationEvent = dauphin.NonNull('StepMaterializationEvent')
    runOrError = dauphin.NonNull('PipelineRunOrError')

    def resolve_materializationEvent(self, graphene_info):
        return graphene_info.schema.type_named('StepMaterializationEvent')(
            materialization=self._event.dagster_event.step_materialization_data.materialization,
            **construct_basic_params(self._event, None)
        )

    def resolve_runOrError(self, graphene_info):
        return get_run_by_id(graphene_info, self._event.run_id)


class DauphinAssetsNotSupportedError(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetsNotSupportedError'
        interfaces = (DauphinError,)


class DauphinAssetsOrError(dauphin.Union):
    class Meta(object):
        name = 'AssetsOrError'
        types = ('AssetConnection', 'AssetsNotSupportedError')


class DauphinAssetConnection(dauphin.ObjectType):
    class Meta(object):
        name = 'AssetConnection'

    nodes = dauphin.non_null_list('Asset')


class DauphinAssetOrError(dauphin.Union):
    class Meta(object):
        name = 'AssetOrError'
        types = ('Asset', 'AssetsNotSupportedError')
