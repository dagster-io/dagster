from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import AbstractSet, Any, NamedTuple  # noqa: UP035

import lkml
import yaml
from dagster import AssetSpec
from dagster._core.utils import toposort_flatten

from dagster_looker.lkml.dagster_looker_lkml_translator import (
    DagsterLookerLkmlTranslator,
    LookMLStructureType,
)


def deep_merge_objs(onto_obj: Any, from_obj: Any) -> Any:
    """Deep merge, which on dictionaries merges keys, and on lists appends elements.
    If a value is present in both onto_obj and from_obj, the value from from_obj is taken.
    For lists, entries are deduplicated by "name" key, resolving conflicts in favor of from_obj.
    """
    # We use ... as a sentinel value for "no value", since we want to distinguish between
    # None and "no value" - None values in the from_obj should override onto_obj values,
    # but if from_obj has no value, we should keep the onto_obj value.
    if isinstance(onto_obj, dict):
        if from_obj in (None, ...):
            return onto_obj
        if not isinstance(from_obj, dict):
            raise Exception("Cannot merge a dictionary with a non-dictionary object")

        result = {
            key: deep_merge_objs(onto_obj.get(key, ...), from_obj.get(key, ...))
            for key in onto_obj.keys() | from_obj.keys()
        }

        return result
    elif isinstance(onto_obj, list):
        if from_obj in (None, ...):
            return onto_obj
        if not isinstance(from_obj, list):
            raise Exception("Cannot merge a list with a non-list object")

        from_obj_names = [
            obj["name"] for obj in from_obj if isinstance(obj, dict) and "name" in obj
        ]
        result = [
            obj
            for obj in onto_obj
            if not isinstance(obj, dict) or obj.get("name") not in from_obj_names
        ] + from_obj

        return result
    else:
        if from_obj is not ...:
            return from_obj
        elif onto_obj is not ...:
            return onto_obj
        else:
            return None


class LookMLStructure(NamedTuple):
    path: Path
    structure_type: LookMLStructureType
    props: Mapping[str, Any]


def postprocess_loaded_structures(
    structs: list[LookMLStructure],
) -> list[LookMLStructure]:
    """Postprocesses LookML structs to resolve refinements and extends.

    https://cloud.google.com/looker/docs/lookml-refinements
    https://cloud.google.com/looker/docs/reusing-code-with-extends
    """
    refined_objs_by_name = {}
    for path, typ, obj_props in structs:
        obj_name = obj_props["name"]
        if not obj_name.startswith("+"):
            refined_objs_by_name[obj_name] = (path, typ, obj_props)

    # Process refinements
    for path, typ, obj_props in structs:
        obj_name = obj_props["name"]
        if obj_name.startswith("+") and obj_name[1:] in refined_objs_by_name:
            refined_objs_by_name[obj_name[1:]] = (
                path,
                typ,
                deep_merge_objs(
                    deep_merge_objs(refined_objs_by_name[obj_name[1:]][2], obj_props),
                    {"name": obj_name[1:]},
                ),
            )

    # Process extends in topological order
    extension_graph: Mapping[str, AbstractSet[str]] = {
        obj_props["name"]: set(obj_props.get("extends__all", [[]])[0])
        for _, _, obj_props in refined_objs_by_name.values()
    }
    evaluation_order = toposort_flatten(extension_graph)

    refined_extended_objs_by_name = {}
    for obj_name in evaluation_order:
        base_obj = refined_objs_by_name[obj_name]
        _, _, obj_props = base_obj
        extensions = obj_props.get("extends__all", [[]])[0]

        output_props = obj_props
        # Merge extensions in reverse order, so that the last extension takes precedence
        # https://cloud.google.com/looker/docs/reusing-code-with-extends#extending_more_than_one_object_at_the_same_time
        for extension in reversed(extensions):
            extension_obj = refined_extended_objs_by_name[extension]
            _, _, extension_props = extension_obj
            output_props = deep_merge_objs(extension_props, output_props)

        refined_extended_objs_by_name[obj_name] = (base_obj[0], base_obj[1], output_props)

    return list(refined_extended_objs_by_name.values())


def build_looker_dashboard_specs(
    project_dir: Path,
    dagster_looker_translator: DagsterLookerLkmlTranslator,
) -> Sequence[AssetSpec]:
    looker_dashboard_specs: list[AssetSpec] = []

    # https://cloud.google.com/looker/docs/reference/param-lookml-dashboard
    for lookml_dashboard_path in project_dir.rglob("*.dashboard.lookml"):
        for lookml_dashboard_props in yaml.safe_load(lookml_dashboard_path.read_bytes()):
            lookml_dashboard = LookMLStructure(
                path=lookml_dashboard_path, structure_type="dashboard", props=lookml_dashboard_props
            )

            looker_dashboard_specs.append(
                dagster_looker_translator.get_asset_spec(lookml_dashboard)
            )

    return looker_dashboard_specs


def build_looker_explore_specs(
    project_dir: Path,
    dagster_looker_translator: DagsterLookerLkmlTranslator,
) -> Sequence[AssetSpec]:
    looker_explore_specs: list[AssetSpec] = []

    explores = []
    # https://cloud.google.com/looker/docs/reference/param-explore
    for lookml_model_path in project_dir.rglob("*.model.lkml"):
        for lookml_explore_props in lkml.load(lookml_model_path.read_text()).get("explores", []):
            lookml_explore = LookMLStructure(
                path=lookml_model_path, structure_type="explore", props=lookml_explore_props
            )
            explores.append(lookml_explore)

    explores_postprocessed = postprocess_loaded_structures(explores)
    for lookml_explore in explores_postprocessed:
        looker_explore_specs.append(dagster_looker_translator.get_asset_spec(lookml_explore))

    return looker_explore_specs


def build_looker_view_specs(
    project_dir: Path,
    dagster_looker_translator: DagsterLookerLkmlTranslator,
) -> Sequence[AssetSpec]:
    looker_view_specs: list[AssetSpec] = []

    # https://cloud.google.com/looker/docs/reference/param-view
    views = []
    for lookml_view_path in project_dir.rglob("*.view.lkml"):
        for lookml_view_props in lkml.load(lookml_view_path.read_text()).get("views", []):
            lookml_view = (lookml_view_path, "view", lookml_view_props)
            views.append(lookml_view)
    views_postprocessed = postprocess_loaded_structures(views)

    for lookml_view in views_postprocessed:
        looker_view_specs.append(dagster_looker_translator.get_asset_spec(lookml_view))

    return looker_view_specs
