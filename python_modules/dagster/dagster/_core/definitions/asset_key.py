import re
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
import dagster._seven as seven
from dagster._annotations import PublicAttr
from dagster._serdes import whitelist_for_serdes

ASSET_KEY_SPLIT_REGEX = re.compile("[^a-zA-Z0-9_]")
ASSET_KEY_DELIMITER = "/"

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.source_asset import SourceAsset


def parse_asset_key_string(s: str) -> Sequence[str]:
    return list(filter(lambda x: x, re.split(ASSET_KEY_SPLIT_REGEX, s)))


@whitelist_for_serdes
class AssetKey(NamedTuple("_AssetKey", [("path", PublicAttr[Sequence[str]])])):
    """Object representing the structure of an asset key.  Takes in a sanitized string, list of
    strings, or tuple of strings.

    Example usage:

    .. code-block:: python

        from dagster import op

        @op
        def emit_metadata(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey('flat_asset_key'),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

        @op
        def structured_asset_key(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey(['parent', 'child', 'grandchild']),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

        @op
        def structured_asset_key_2(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey(('parent', 'child', 'grandchild')),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

    Args:
        path (Sequence[str]): String, list of strings, or tuple of strings.  A list of strings
            represent the hierarchical structure of the asset_key.
    """

    def __new__(cls, path: Sequence[str]):
        if isinstance(path, str):
            path = [path]
        else:
            path = list(check.sequence_param(path, "path", of_type=str))

        return super(AssetKey, cls).__new__(cls, path=path)

    def __str__(self):
        return f"AssetKey({self.path})"

    def __repr__(self):
        return f"AssetKey({self.path})"

    def __hash__(self):
        return hash(tuple(self.path))

    def __eq__(self, other):
        if not isinstance(other, AssetKey):
            return False
        if len(self.path) != len(other.path):
            return False
        for i in range(0, len(self.path)):
            if self.path[i] != other.path[i]:
                return False
        return True

    def to_string(self) -> str:
        """E.g. '["first_component", "second_component"]'."""
        return seven.json.dumps(self.path)

    def to_user_string(self) -> str:
        """E.g. "first_component/second_component"."""
        return ASSET_KEY_DELIMITER.join(self.path)

    def to_python_identifier(self, suffix: Optional[str] = None) -> str:
        """Build a valid Python identifier based on the asset key that can be used for
        operation names or I/O manager keys.
        """
        path = list(self.path)

        if suffix is not None:
            path.append(suffix)

        return "__".join(path).replace("-", "_")

    @staticmethod
    def from_user_string(asset_key_string: str) -> "AssetKey":
        return AssetKey(asset_key_string.split(ASSET_KEY_DELIMITER))

    @staticmethod
    def from_db_string(asset_key_string: Optional[str]) -> Optional["AssetKey"]:
        if not asset_key_string:
            return None
        if asset_key_string[0] == "[":
            # is a json string
            try:
                path = seven.json.loads(asset_key_string)
            except seven.JSONDecodeError:
                path = parse_asset_key_string(asset_key_string)
        else:
            path = parse_asset_key_string(asset_key_string)
        return AssetKey(path)

    @staticmethod
    def get_db_prefix(path: Sequence[str]):
        check.sequence_param(path, "path", of_type=str)
        return seven.json.dumps(path)[:-2]  # strip trailing '"]' from json string

    @staticmethod
    def from_graphql_input(graphql_input_asset_key: Mapping[str, Sequence[str]]) -> "AssetKey":
        return AssetKey(graphql_input_asset_key["path"])

    def to_graphql_input(self) -> Mapping[str, Sequence[str]]:
        return {"path": self.path}

    @staticmethod
    def from_coercible(arg: "CoercibleToAssetKey") -> "AssetKey":
        if isinstance(arg, AssetKey):
            return check.inst_param(arg, "arg", AssetKey)
        elif isinstance(arg, str):
            return AssetKey([arg])
        elif isinstance(arg, list):
            check.list_param(arg, "arg", of_type=str)
            return AssetKey(arg)
        elif isinstance(arg, tuple):
            check.tuple_param(arg, "arg", of_type=str)
            return AssetKey(arg)
        else:
            check.failed(f"Unexpected type for AssetKey: {type(arg)}")

    @staticmethod
    def from_coercible_or_definition(
        arg: Union["CoercibleToAssetKey", "AssetsDefinition", "SourceAsset"],
    ) -> "AssetKey":
        from dagster._core.definitions.assets import AssetsDefinition
        from dagster._core.definitions.source_asset import SourceAsset

        if isinstance(arg, AssetsDefinition):
            return arg.key
        elif isinstance(arg, SourceAsset):
            return arg.key
        else:
            return AssetKey.from_coercible(arg)

    def has_prefix(self, prefix: Sequence[str]) -> bool:
        return len(self.path) >= len(prefix) and self.path[: len(prefix)] == prefix

    def with_prefix(self, prefix: "CoercibleToAssetKeyPrefix") -> "AssetKey":
        prefix = key_prefix_from_coercible(prefix)
        return AssetKey(list(prefix) + list(self.path))


CoercibleToAssetKey = Union[AssetKey, str, Sequence[str]]
CoercibleToAssetKeyPrefix = Union[str, Sequence[str]]


def check_opt_coercible_to_asset_key_prefix_param(
    prefix: Optional[CoercibleToAssetKeyPrefix], param_name: str
) -> Optional[Sequence[str]]:
    try:
        return key_prefix_from_coercible(prefix) if prefix is not None else None
    except check.CheckError:
        raise check.ParameterCheckError(
            f'Param "{param_name}" is not a string or a sequence of strings'
        )


def key_prefix_from_coercible(key_prefix: CoercibleToAssetKeyPrefix) -> Sequence[str]:
    if isinstance(key_prefix, str):
        return [key_prefix]
    elif isinstance(key_prefix, list):
        return key_prefix
    else:
        check.failed(f"Unexpected type for key_prefix: {type(key_prefix)}")
