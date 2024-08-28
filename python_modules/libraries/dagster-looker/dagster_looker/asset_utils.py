from pathlib import Path
from typing import List, Sequence

import lkml
import yaml
from dagster import AssetSpec

from dagster_looker.dagster_looker_translator import DagsterLookerTranslator


def build_looker_dashboard_specs(
    project_dir: Path,
    dagster_looker_translator: DagsterLookerTranslator,
) -> Sequence[AssetSpec]:
    looker_dashboard_specs: List[AssetSpec] = []

    # https://cloud.google.com/looker/docs/reference/param-lookml-dashboard
    for lookml_dashboard_path in project_dir.rglob("*.dashboard.lookml"):
        for lookml_dashboard_props in yaml.safe_load(lookml_dashboard_path.read_bytes()):
            lookml_dashboard = (lookml_dashboard_path, "dashboard", lookml_dashboard_props)

            looker_dashboard_specs.append(
                AssetSpec(
                    key=dagster_looker_translator.get_asset_key(lookml_dashboard),
                    deps=dagster_looker_translator.get_deps(lookml_dashboard),
                    description=dagster_looker_translator.get_description(lookml_dashboard),
                    metadata=dagster_looker_translator.get_metadata(lookml_dashboard),
                    group_name=dagster_looker_translator.get_group_name(lookml_dashboard),
                    owners=dagster_looker_translator.get_owners(lookml_dashboard),
                    tags=dagster_looker_translator.get_tags(lookml_dashboard),
                )
            )

    return looker_dashboard_specs


def build_looker_explore_specs(
    project_dir: Path,
    dagster_looker_translator: DagsterLookerTranslator,
) -> Sequence[AssetSpec]:
    looker_explore_specs: List[AssetSpec] = []

    # https://cloud.google.com/looker/docs/reference/param-explore
    for lookml_model_path in project_dir.rglob("*.model.lkml"):
        for lookml_explore_props in lkml.load(lookml_model_path.read_text()).get("explores", []):
            lookml_explore = (lookml_model_path, "explore", lookml_explore_props)

            looker_explore_specs.append(
                AssetSpec(
                    key=dagster_looker_translator.get_asset_key(lookml_explore),
                    deps=dagster_looker_translator.get_deps(lookml_explore),
                    description=dagster_looker_translator.get_description(lookml_explore),
                    metadata=dagster_looker_translator.get_metadata(lookml_explore),
                    group_name=dagster_looker_translator.get_group_name(lookml_explore),
                    owners=dagster_looker_translator.get_owners(lookml_explore),
                    tags=dagster_looker_translator.get_tags(lookml_explore),
                )
            )

    return looker_explore_specs


def build_looker_view_specs(
    project_dir: Path,
    dagster_looker_translator: DagsterLookerTranslator,
) -> Sequence[AssetSpec]:
    looker_view_specs: List[AssetSpec] = []

    # https://cloud.google.com/looker/docs/reference/param-view
    for lookml_view_path in project_dir.rglob("*.view.lkml"):
        for lookml_view_props in lkml.load(lookml_view_path.read_text()).get("views", []):
            lookml_view = (lookml_view_path, "view", lookml_view_props)

            looker_view_specs.append(
                AssetSpec(
                    key=dagster_looker_translator.get_asset_key(lookml_view),
                    deps=dagster_looker_translator.get_deps(lookml_view),
                    description=dagster_looker_translator.get_description(lookml_view),
                    metadata=dagster_looker_translator.get_metadata(lookml_view),
                    group_name=dagster_looker_translator.get_group_name(lookml_view),
                    owners=dagster_looker_translator.get_owners(lookml_view),
                    tags=dagster_looker_translator.get_tags(lookml_view),
                )
            )

    return looker_view_specs
