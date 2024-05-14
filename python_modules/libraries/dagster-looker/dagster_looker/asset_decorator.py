import itertools
import logging
import re
from pathlib import Path
from typing import AbstractSet, Any, Callable, Iterator, Mapping, Optional, Sequence, cast

import lkml
import yaml
from dagster import AssetKey, AssetsDefinition, AssetSpec, multi_asset
from dagster._annotations import experimental
from sqlglot import exp, parse_one, to_table
from sqlglot.optimizer import Scope, build_scope, optimize

logger = logging.getLogger("dagster_looker")


def build_looker_explore_specs(project_dir: Path) -> Sequence[AssetSpec]:
    looker_explore_specs = []

    # https://cloud.google.com/looker/docs/reference/param-explore
    for model_path in project_dir.rglob("*.model.lkml"):
        for explore in lkml.load(model_path.read_text()).get("explores", []):
            explore_asset_key = AssetKey(["explore", explore["name"]])

            # https://cloud.google.com/looker/docs/reference/param-explore-from
            explore_base_view = [{"name": explore.get("from") or explore["name"]}]

            # https://cloud.google.com/looker/docs/reference/param-explore-join
            explore_join_views: Sequence[Mapping[str, Any]] = explore.get("joins", [])

            looker_explore_specs.append(
                AssetSpec(
                    key=explore_asset_key,
                    deps={
                        AssetKey(["view", view["name"]])
                        for view in itertools.chain(explore_base_view, explore_join_views)
                    },
                )
            )

    return looker_explore_specs


def build_asset_key_from_sqlglot_table(table: exp.Table) -> AssetKey:
    return AssetKey([part.name.replace("*", "_star") for part in table.parts])


def parse_upstream_asset_keys_from_looker_view(
    looker_view: Mapping[str, Any], looker_view_path: Path
) -> AbstractSet[AssetKey]:
    sql_dialect = "bigquery"

    # https://cloud.google.com/looker/docs/derived-tables
    derived_table_sql: Optional[str] = looker_view.get("derived_table", {}).get("sql")
    if not derived_table_sql:
        # https://cloud.google.com/looker/docs/reference/param-view-sql-table-name
        sql_table_name = looker_view.get("sql_table_name") or looker_view["name"]
        sqlglot_table = to_table(sql_table_name.replace("`", ""), dialect=sql_dialect)

        return {build_asset_key_from_sqlglot_table(sqlglot_table)}

    # We need to handle the Looker substitution operator ($) properly since the lkml
    # compatible SQL may not be parsable yet by sqlglot.
    #
    # https://cloud.google.com/looker/docs/sql-and-referring-to-lookml#substitution_operator_
    upstream_view_pattern = re.compile(r"\${(.*?)\.SQL_TABLE_NAME\}")
    if upstream_looker_views_from_substitution := upstream_view_pattern.findall(derived_table_sql):
        return {
            AssetKey(["view", upstream_looker_view_name])
            for upstream_looker_view_name in upstream_looker_views_from_substitution
        }

    upstream_sqlglot_tables: Sequence[exp.Table] = []
    try:
        optimized_derived_table_ast = optimize(
            parse_one(sql=derived_table_sql, dialect=sql_dialect),
            dialect=sql_dialect,
            validate_qualify_columns=False,
        )
        root_scope = build_scope(optimized_derived_table_ast)

        upstream_sqlglot_tables = [
            source
            for scope in cast(Iterator[Scope], root_scope.traverse() if root_scope else [])
            for (_, source) in scope.selected_sources.values()
            if isinstance(source, exp.Table)
        ]
    except Exception as e:
        logger.warn(
            f"Failed to optimize derived table SQL for view `{looker_view['name']}`"
            f" in file `{looker_view_path.name}`."
            " The upstream dependencies for the view will be omitted.\n\n"
            f"Exception: {e}"
        )

    return {build_asset_key_from_sqlglot_table(table) for table in upstream_sqlglot_tables}


def build_looker_view_specs(project_dir: Path) -> Sequence[AssetSpec]:
    looker_view_specs = []

    # https://cloud.google.com/looker/docs/reference/param-view
    for looker_view_path in project_dir.rglob("*.view.lkml"):
        for looker_view in lkml.load(looker_view_path.read_text()).get("views", []):
            looker_view_specs.append(
                AssetSpec(
                    key=AssetKey(["view", looker_view["name"]]),
                    deps=parse_upstream_asset_keys_from_looker_view(looker_view, looker_view_path),
                )
            )

    return looker_view_specs


@experimental
def looker_assets(*, project_dir: Path) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """A decorator for defining Looker assets in a project.

    Args:
        project_dir (Path): The path to the Looker project directory.

    Examples:
        .. code-block:: python

            from pathlib import Path

            from dagster_looker import looker_assets

            @looker_assets(project_dir=Path("my_looker_project"))
            def my_looker_project_assets(): ...
    """
    lookml_dashboard_specs = [
        AssetSpec(
            key=AssetKey(["dashboard", lookml_dashboard["dashboard"]]),
            deps={AssetKey(["explore", dashboard_element["explore"]])},
        )
        for dashboard_path in project_dir.rglob("*.dashboard.lookml")
        # Each dashboard file can contain multiple dashboards.
        for lookml_dashboard in yaml.safe_load(dashboard_path.read_bytes())
        # For each dashboard, we create an asset. An `explore` in the dashboard is a dependency.
        for dashboard_element in itertools.chain(
            lookml_dashboard.get("elements", []),
            lookml_dashboard.get("filters", []),
        )
        if dashboard_element.get("explore")
    ]

    return multi_asset(
        compute_kind="looker",
        specs=[
            *lookml_dashboard_specs,
            *build_looker_explore_specs(project_dir),
            *build_looker_view_specs(project_dir),
        ],
    )
