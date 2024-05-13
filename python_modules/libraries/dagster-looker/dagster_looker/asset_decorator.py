import itertools
import logging
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence, cast

import lkml
import yaml
from dagster import AssetKey, AssetsDefinition, AssetSpec, multi_asset
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


def build_looker_view_specs(project_dir: Path) -> Sequence[AssetSpec]:
    looker_view_specs = []
    sql_dialect = "bigquery"

    # https://cloud.google.com/looker/docs/reference/param-view
    for view_path in project_dir.rglob("*.view.lkml"):
        for view in lkml.load(view_path.read_text()).get("views", []):
            upstream_tables: Sequence[exp.Table] = [to_table(view["name"], dialect=sql_dialect)]

            # https://cloud.google.com/looker/docs/derived-tables
            derived_table_sql = view.get("derived_table", {}).get("sql")

            if derived_table_sql and "$" in derived_table_sql:
                logger.warn(
                    f"Failed to parse the derived table SQL for view `{view['name']}`"
                    f" in file {view_path.name}, because the SQL in this view contains the"
                    " LookML substitution operator, `$`."
                    " The upstream dependencies for the view will be omitted."
                )

                upstream_tables = []
            elif (
                derived_table_sql
                # We need to handle the Looker substitution operator ($) properly since the lkml
                # compatible SQL may not be parsable yet by sqlglot.
                #
                # https://cloud.google.com/looker/docs/sql-and-referring-to-lookml#substitution_operator_
                and "$" not in derived_table_sql
            ):
                try:
                    optimized_derived_table_ast = optimize(
                        parse_one(sql=derived_table_sql, dialect=sql_dialect),
                        dialect=sql_dialect,
                        validate_qualify_columns=False,
                    )
                    root_scope = build_scope(optimized_derived_table_ast)

                    upstream_tables = [
                        source
                        for scope in cast(
                            Iterator[Scope], root_scope.traverse() if root_scope else []
                        )
                        for (_, source) in scope.selected_sources.values()
                        if isinstance(source, exp.Table)
                    ]
                except Exception as e:
                    logger.warn(
                        f"Failed to optimize derived table SQL for view `{view['name']}`"
                        f" in file {view_path.name}."
                        " The upstream dependencies for the view will be omitted.\n\n"
                        f"Exception: {e}"
                    )

                    upstream_tables = []

            # https://cloud.google.com/looker/docs/reference/param-view-sql-table-name
            elif sql_table_name := view.get("sql_table_name"):
                upstream_tables = [to_table(sql_table_name.replace("`", ""), dialect=sql_dialect)]

            looker_view_specs.append(
                AssetSpec(
                    key=AssetKey(["view", view["name"]]),
                    deps={
                        AssetKey([part.name.replace("*", "_star") for part in table.parts])
                        for table in upstream_tables
                    },
                )
            )

    return looker_view_specs


def looker_assets(*, project_dir: Path) -> Callable[[Callable[..., Any]], AssetsDefinition]:
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
