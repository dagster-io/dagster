import itertools
import logging
import re
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Callable, Literal, Optional, cast

from dagster import AssetKey, AssetSpec
from dagster._annotations import beta, public, superseded
from dagster._utils.warnings import supersession_warning
from sqlglot import ParseError, exp, parse_one, to_table
from sqlglot.optimizer import Scope, build_scope, optimize

from dagster_looker.lkml.liquid_utils import best_effort_render_liquid_sql
from dagster_looker.lkml.sqlglot_utils import custom_bigquery_dialect_inst

LookMLStructureType = Literal["dashboard", "explore", "table", "view"]

logger = logging.getLogger("dagster_looker")


def build_deps_for_looker_dashboard(
    dagster_looker_translator: "DagsterLookerLkmlTranslator",
    lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]],
) -> Sequence[AssetKey]:
    lookml_view_path, _, lookml_dashboard_props = lookml_structure

    return list(
        {
            dagster_looker_translator.get_asset_spec(
                lookml_structure=(
                    lookml_view_path,
                    "explore",
                    lookml_element_from_dashboard_props,
                )
            ).key
            for lookml_element_from_dashboard_props in itertools.chain(
                # https://cloud.google.com/looker/docs/reference/param-lookml-dashboard#elements_2
                lookml_dashboard_props.get("elements", []),
                # https://cloud.google.com/looker/docs/reference/param-lookml-dashboard#filters
                lookml_dashboard_props.get("filters", []),
            )
            if lookml_element_from_dashboard_props.get("explore")
        }
    )


def build_deps_for_looker_explore(
    dagster_looker_translator: "DagsterLookerLkmlTranslator",
    lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]],
) -> Sequence[AssetKey]:
    lookml_explore_path, _, lookml_explore_props = lookml_structure

    # https://cloud.google.com/looker/docs/reference/param-explore-from
    explore_base_view = [{"name": lookml_explore_props.get("from") or lookml_explore_props["name"]}]

    # https://cloud.google.com/looker/docs/reference/param-explore-join
    explore_join_views: Sequence[Mapping[str, Any]] = lookml_explore_props.get("joins", [])

    return list(
        {
            dagster_looker_translator.get_asset_spec(
                lookml_structure=(
                    lookml_explore_path,
                    "view",
                    lookml_view_from_explore_props,
                )
            ).key
            for lookml_view_from_explore_props in itertools.chain(
                explore_base_view, explore_join_views
            )
        }
    )


def build_deps_for_looker_view(
    dagster_looker_translator: "DagsterLookerLkmlTranslator",
    lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]],
) -> Sequence[AssetKey]:
    lookml_view_path, _, lookml_view_props = lookml_structure

    # https://cloud.google.com/looker/docs/derived-tables
    derived_table_sql: Optional[str] = lookml_view_props.get("derived_table", {}).get("sql")
    if not derived_table_sql:
        # https://cloud.google.com/looker/docs/reference/param-view-sql-table-name
        sql_table_name = lookml_view_props.get("sql_table_name") or lookml_view_props["name"]
        try:
            sqlglot_table = to_table(
                sql_table_name.replace("`", ""), dialect=custom_bigquery_dialect_inst
            )
        except ParseError as e:
            logger.warn(
                f"Failed to parse derived table SQL for view `{sql_table_name}`"
                f" in file `{lookml_view_path.name}`."
                " The upstream dependencies for the view will be omitted.\n\n"
                f"Exception: {e}"
            )
            return []

        return [
            dagster_looker_translator.get_asset_spec(
                lookml_structure=(
                    lookml_view_path,
                    "table",
                    {"table": sqlglot_table, "from_structure": lookml_view_props},
                )
            ).key
        ]

    # We need to handle the Looker substitution operator ($) properly since the lkml
    # compatible SQL may not be parsable yet by sqlglot.
    #
    # https://cloud.google.com/looker/docs/sql-and-referring-to-lookml#substitution_operator_
    upstream_view_pattern = re.compile(r"\${(.*?)\.SQL_TABLE_NAME\}")
    if upstream_looker_views_from_substitution := upstream_view_pattern.findall(derived_table_sql):
        return [
            dagster_looker_translator.get_asset_spec(
                lookml_structure=(
                    lookml_view_path,
                    "view",
                    {"name": upstream_looker_view_name},
                )
            ).key
            for upstream_looker_view_name in set(upstream_looker_views_from_substitution)
        ]

    upstream_sqlglot_tables: Sequence[exp.Table] = []
    try:
        rendered_liquid_sql = best_effort_render_liquid_sql(
            lookml_view_props["name"], lookml_view_path.name, derived_table_sql
        )
        parsed_derived_table_ast = parse_one(
            sql=rendered_liquid_sql, dialect=custom_bigquery_dialect_inst
        )
        ast_to_evaluate = parsed_derived_table_ast
        try:
            optimized_derived_table_ast = optimize(
                parsed_derived_table_ast,
                dialect=custom_bigquery_dialect_inst,
                validate_qualify_columns=False,
            )
            ast_to_evaluate = optimized_derived_table_ast
        except ParseError:
            pass
        root_scope = build_scope(ast_to_evaluate)

        upstream_sqlglot_tables = [
            source
            for scope in cast(Iterator[Scope], root_scope.traverse() if root_scope else [])
            for (_, source) in scope.selected_sources.values()
            if isinstance(source, exp.Table)
        ]
    except Exception as e:
        logger.warn(
            f"Failed to parse derived table SQL for view `{lookml_view_props['name']}`"
            f" in file `{lookml_view_path.name}`."
            " The upstream dependencies for the view will be omitted.\n\n"
            f"Exception: {e}"
        )

    return list(
        {
            dagster_looker_translator.get_asset_spec(
                lookml_structure=(
                    lookml_view_path,
                    "table",
                    {"table": sqlglot_table, "from_structure": lookml_view_props},
                )
            ).key
            for sqlglot_table in upstream_sqlglot_tables
        }
    )


@beta
class DagsterLookerLkmlTranslator:
    """Holds a set of methods that derive Dagster asset definition metadata given a representation
    of a LookML structure (dashboards, explores, views).

    This class is exposed so that methods can be overridden to customize how Dagster asset metadata
    is derived.
    """

    @public
    def get_asset_spec(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> AssetSpec:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster asset spec that represents the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide a custom asset spec for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            AssetSpec: The Dagster asset spec that represents the LookML structure.
        """
        return AssetSpec(
            key=self._resolve_back_compat_method(
                "get_asset_key", self._default_asset_key_fn, lookml_structure
            ),
            deps=self._resolve_back_compat_method(
                "get_deps", self._default_deps_fn, lookml_structure
            ),
            description=self._resolve_back_compat_method(
                "get_description", self._default_description_fn, lookml_structure
            ),
            metadata=self._resolve_back_compat_method(
                "get_metadata", self._default_metadata_fn, lookml_structure
            ),
            group_name=self._resolve_back_compat_method(
                "get_group_name", self._default_group_name_fn, lookml_structure
            ),
            owners=self._resolve_back_compat_method(
                "get_owners", self._default_owners_fn, lookml_structure
            ),
            tags=self._resolve_back_compat_method(
                "get_tags", self._default_tags_fn, lookml_structure
            ),
        )

    def _resolve_back_compat_method(
        self,
        method_name: str,
        default_fn: Callable[[tuple[Path, LookMLStructureType, Mapping[str, Any]]], Any],
        lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]],
    ):
        method = getattr(type(self), method_name)
        base_method = getattr(DagsterLookerLkmlTranslator, method_name)
        if method is not base_method:  # user defined this
            supersession_warning(
                subject=method_name,
                additional_warn_text=(
                    f"Instead of overriding DagsterLookerLkmlTranslator.{method_name}(), "
                    f"override DagsterLookerLkmlTranslator.get_asset_spec()."
                ),
            )
            return method(self, lookml_structure)
        else:
            return default_fn(lookml_structure)

    @superseded(
        additional_warn_text="Use `DagsterLookerLkmlTranslator.get_asset_spec(...).key` instead.",
    )
    @public
    def get_asset_key(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> AssetKey:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster asset key that represents the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide a custom asset key for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            AssetKey: The Dagster asset key that represents the LookML structure.
        """
        return self._default_asset_key_fn(lookml_structure)

    def _default_asset_key_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> AssetKey:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster asset key that represents the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            AssetKey: The Dagster asset key that represents the LookML structure.
        """
        lookml_structure_path, lookml_structure_type, lookml_structure_props = lookml_structure

        if lookml_structure_type == "dashboard":
            return AssetKey(["dashboard", lookml_structure_props["dashboard"]])

        if lookml_structure_type == "view":
            return AssetKey(["view", lookml_structure_props["name"]])

        if lookml_structure_type == "table":
            sqlglot_table = lookml_structure_props["table"]

            return AssetKey([part.name.replace("*", "_star") for part in sqlglot_table.parts])

        if lookml_structure_type == "explore":
            explore_name = lookml_structure_props.get("explore") or lookml_structure_props.get(
                "name"
            )

            if not explore_name:
                raise ValueError(
                    f"Could not find `name` or `explore` property in LookML structure type `{lookml_structure_type}`"
                    f" at path `{lookml_structure_path}` with properties {lookml_structure_props}"
                )

            return AssetKey(["explore", explore_name])

        raise ValueError(
            f"Unsupported LookML structure type `{lookml_structure_type}` at path `{lookml_structure_path}`"
        )

    @superseded(
        additional_warn_text=(
            "Iterate over `DagsterLookerLkmlTranslator.get_asset_spec(...).deps` "
            "to access `AssetDep.asset_key` instead."
        ),
    )
    @public
    def get_deps(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Sequence[AssetKey]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster dependencies of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide custom dependencies for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Sequence[AssetKey]: The Dagster dependencies for the LookML structure.
        """
        return self._default_deps_fn(lookml_structure)

    def _default_deps_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Sequence[AssetKey]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster dependencies of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Sequence[AssetKey]: The Dagster dependencies for the LookML structure.
        """
        lookml_structure_path, lookml_structure_type, _ = lookml_structure

        if lookml_structure_type == "dashboard":
            return build_deps_for_looker_dashboard(
                dagster_looker_translator=self, lookml_structure=lookml_structure
            )

        if lookml_structure_type == "explore":
            return build_deps_for_looker_explore(
                dagster_looker_translator=self, lookml_structure=lookml_structure
            )

        if lookml_structure_type == "view":
            return build_deps_for_looker_view(
                dagster_looker_translator=self, lookml_structure=lookml_structure
            )

        if lookml_structure_type == "table":
            return []

        raise ValueError(
            f"Unsupported LookML structure type `{lookml_structure_type}` at path `{lookml_structure_path}`"
        )

    @superseded(
        additional_warn_text="Use `DagsterLookerLkmlTranslator.get_asset_spec(...).description` instead.",
    )
    @public
    def get_description(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[str]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster description of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide a custom description for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[str]: The Dagster description for the LookML structure.
        """
        return self._default_description_fn(lookml_structure)

    def _default_description_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[str]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster description of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[str]: The Dagster description for the LookML structure.
        """
        _, _, lookml_structure_props = lookml_structure

        return lookml_structure_props.get("description")

    @superseded(
        additional_warn_text="Use `DagsterLookerLkmlTranslator.get_asset_spec(...).metadata` instead.",
    )
    @public
    def get_metadata(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[Mapping[str, Any]]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster metadata of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide custom metadata for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[Mapping[str, Any]]: A dictionary representing the Dagster metadata for the
                LookML structure.
        """
        return self._default_metadata_fn(lookml_structure)

    @public
    def _default_metadata_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[Mapping[str, Any]]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster metadata of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[Mapping[str, Any]]: A dictionary representing the Dagster metadata for the
                LookML structure.
        """
        return None

    @superseded(
        additional_warn_text="Use `DagsterLookerLkmlTranslator.get_asset_spec(...).group_name` instead.",
    )
    @public
    def get_group_name(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[str]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster group name of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide a custom group name for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[str]: A Dagster group name for the LookML structure.
        """
        return self._default_group_name_fn(lookml_structure)

    def _default_group_name_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[str]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster group name of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[str]: A Dagster group name for the LookML structure.
        """
        return None

    @superseded(
        additional_warn_text="Use `DagsterLookerLkmlTranslator.get_asset_spec(...).owners` instead.",
    )
    @public
    def get_owners(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[Sequence[str]]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster owners of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide custom owners for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[Sequence[str]]: A sequence of Dagster owners for the LookML structure.
        """
        return self._default_owners_fn(lookml_structure)

    def _default_owners_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[Sequence[str]]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster owners of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[Sequence[str]]: A sequence of Dagster owners for the LookML structure.
        """
        return None

    @superseded(
        additional_warn_text="Use `DagsterLookerLkmlTranslator.get_asset_spec(...).tags` instead.",
    )
    @public
    def get_tags(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[Mapping[str, str]]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster tags of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overridden to provide custom tags for a LookML structure.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[Mapping[str, str]]: A dictionary representing the Dagster tags for the
                LookML structure.
        """
        return self._default_tags_fn(lookml_structure)

    def _default_tags_fn(
        self, lookml_structure: tuple[Path, LookMLStructureType, Mapping[str, Any]]
    ) -> Optional[Mapping[str, str]]:
        """A method that takes in a LookML structure (dashboards, explores, views) and
        returns the Dagster tags of the structure.

        The LookML structure is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        Args:
            lookml_structure (Tuple[Path, str, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML structure, the LookML structure type, and a dictionary
                representing a LookML structure.

        Returns:
            Optional[Mapping[str, str]]: A dictionary representing the Dagster tags for the
                LookML structure.
        """
        return None
