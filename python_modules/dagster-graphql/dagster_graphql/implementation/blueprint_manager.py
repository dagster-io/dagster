from typing import cast

from dagster._core.definitions.selector import BlueprintManagerSelector
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.external_data import BlueprintKey
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._grpc.types import ModifyBlueprintAction, ModifyBlueprintRequest

from dagster_graphql.schema.util import ResolveInfo


def create_blueprint(
    graphene_info: ResolveInfo, selector: BlueprintManagerSelector, name: str, blob: str
) -> str:
    instance: DagsterInstance = graphene_info.context.instance

    context: WorkspaceRequestContext = graphene_info.context

    location = context.get_code_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    result = cast(GrpcServerCodeLocation, location).client.create_blueprint(
        ModifyBlueprintRequest(
            origin=repository.get_external_origin(),
            instance_ref=instance.get_ref(),
            target=BlueprintKey(
                manager_name=selector.blueprint_manager_name, identifier_within_manager=name
            ),
            action=ModifyBlueprintAction.CREATE,
            blob=blob,
        )
    )

    return result.url


def update_blueprint(
    graphene_info: ResolveInfo, selector: BlueprintManagerSelector, name: str, blob: str
) -> str:
    instance: DagsterInstance = graphene_info.context.instance

    context: WorkspaceRequestContext = graphene_info.context

    location = context.get_code_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    result = cast(GrpcServerCodeLocation, location).client.create_blueprint(
        ModifyBlueprintRequest(
            origin=repository.get_external_origin(),
            instance_ref=instance.get_ref(),
            target=BlueprintKey(
                manager_name=selector.blueprint_manager_name, identifier_within_manager=name
            ),
            action=ModifyBlueprintAction.UPDATE,
            blob=blob,
        )
    )

    return result.url
