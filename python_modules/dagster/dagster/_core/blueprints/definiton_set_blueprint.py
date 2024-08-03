from typing import Any, Generic, List, Mapping, Optional, Sequence

from typing_extensions import TypeVar

from dagster import _check as check
from dagster._core.blueprints.blueprint import Blueprint, BlueprintDefinitions
from dagster._core.definitions.assets import AssetsDefinition
from dagster._model import DagsterModel
from dagster._utils.merger import merge_dicts

T = TypeVar("T", bound=Blueprint)


class OverridableAssetSpecProperties(DagsterModel):
    metadata: Mapping[str, Any] = {}
    group_name: Optional[str] = None
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Mapping[str, str] = {}


class BlueprintDefintionSet(Blueprint, OverridableAssetSpecProperties, Generic[T]):
    """A blueprint that allows customization for a set of definitions,
    provided by nested blueprints.
    """

    contents: List[T]

    def build_defs(self) -> BlueprintDefinitions:
        nested_defs = [nested_blueprint.build_defs() for nested_blueprint in self.contents]
        defs = BlueprintDefinitions.merge(*nested_defs)

        new_assets = []
        for assets_def in defs.assets or []:
            if not isinstance(assets_def, AssetsDefinition):
                new_assets.append(assets_def)
                continue

            spec_keys_to_replace = {}
            spec_keys_to_replace_by_key = {}

            if self.group_name:
                check.invariant(
                    not any(value != "default" for value in assets_def.group_names_by_key.values()),
                    "Definition set does not support overriding group names which are already set in the nested blueprints.",
                )
                spec_keys_to_replace["group_name"] = self.group_name

            if self.code_version:
                check.invariant(
                    not any(assets_def.code_versions_by_key.values()),
                    "Definition set does not support overriding code versions which are already set in the nested blueprints.",
                )
                spec_keys_to_replace["code_version"] = self.code_version

            if self.owners:
                check.invariant(
                    not any(assets_def.owners_by_key.values()),
                    "Definition set does not support overriding owners which are already set in the nested blueprints.",
                )
                spec_keys_to_replace["owners"] = self.owners

            if self.tags:
                spec_keys_to_replace_by_key["tags"] = {
                    k: merge_dicts(assets_def.tags_by_key[k], self.tags) for k in assets_def.keys
                }
            if self.metadata:
                spec_keys_to_replace_by_key["metadata"] = {
                    k: merge_dicts(assets_def.metadata_by_key[k], self.metadata)
                    for k in assets_def.keys
                }

            new_asset_def = AssetsDefinition.dagster_internal_init(
                **{
                    **assets_def.get_attributes_dict(),
                    **{
                        "specs": [
                            spec._replace(
                                **spec_keys_to_replace,
                                **(
                                    {k: v[spec.key] for k, v in spec_keys_to_replace_by_key.items()}
                                ),
                            )
                            for spec in assets_def.specs
                        ]
                    },
                }
            )
            new_assets.append(new_asset_def)

        return defs._replace(assets=new_assets)
