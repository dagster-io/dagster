from typing import Union

import graphene
from dagster._check import invariant
from dagster._core.utils import is_valid_email


class GrapheneUserDefinitionOwner(graphene.ObjectType):
    class Meta:
        name = "UserDefinitionOwner"

    email = graphene.NonNull(graphene.String)


class GrapheneTeamDefinitionOwner(graphene.ObjectType):
    class Meta:
        name = "TeamDefinitionOwner"

    team = graphene.NonNull(graphene.String)


class GrapheneDefinitionOwner(graphene.Union):
    class Meta:
        types = (
            GrapheneUserDefinitionOwner,
            GrapheneTeamDefinitionOwner,
        )
        name = "DefinitionOwner"


def definition_owner_from_owner_str(
    owner_str: str,
) -> Union[GrapheneUserDefinitionOwner, GrapheneTeamDefinitionOwner]:
    if is_valid_email(owner_str):
        return GrapheneUserDefinitionOwner(email=owner_str)
    else:
        invariant(owner_str.startswith("team:"))
        return GrapheneTeamDefinitionOwner(team=owner_str[5:])


# legacy classes for backcompatibility
class GrapheneUserAssetOwner(GrapheneUserDefinitionOwner):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        name = "UserAssetOwner"


class GrapheneTeamAssetOwner(GrapheneTeamDefinitionOwner):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        name = "TeamAssetOwner"


class GrapheneAssetOwner(graphene.Union):
    class Meta:
        types = (
            GrapheneUserAssetOwner,
            GrapheneTeamAssetOwner,
        )
        name = "AssetOwner"
