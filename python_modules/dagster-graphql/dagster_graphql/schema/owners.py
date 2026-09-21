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
) -> GrapheneUserDefinitionOwner | GrapheneTeamDefinitionOwner:
    if is_valid_email(owner_str):
        return GrapheneUserDefinitionOwner(email=owner_str)
    else:
        invariant(owner_str.startswith("team:"))
        return GrapheneTeamDefinitionOwner(team=owner_str[5:])


# legacy classes for backcompatibility
class GrapheneUserAssetOwner(GrapheneUserDefinitionOwner):
    class Meta:
        name = "UserAssetOwner"


class GrapheneTeamAssetOwner(GrapheneTeamDefinitionOwner):
    class Meta:
        name = "TeamAssetOwner"


class GrapheneAssetOwner(graphene.Union):
    class Meta:
        types = (
            GrapheneUserAssetOwner,
            GrapheneTeamAssetOwner,
        )
        name = "AssetOwner"

    @staticmethod
    def to_manifest_dict(owner_str: str) -> dict:
        if is_valid_email(owner_str):
            return {"__typename": "UserAssetOwner", "email": owner_str}
        return {"__typename": "TeamAssetOwner", "team": owner_str[5:]}
