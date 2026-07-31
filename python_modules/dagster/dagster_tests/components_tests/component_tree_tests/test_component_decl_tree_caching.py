"""Regression tests for O(n) component-decl tree materialization on cold load.

Without seeding cacheable child decls after the first tree walk, loading n
components re-materializes the full loc→decl map once per uncached loc
(Θ(n²) walks). These tests pin that cold multi-loc loads stay linear in the
number of tree materializations.
"""

from unittest.mock import patch

import dagster as dg
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.defs_module import ComponentPath
from dagster.components.testing import create_defs_folder_sandbox


class EmptyComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()


def test_cold_build_defs_materializes_component_decl_tree_once() -> None:
    """Cold load of many sibling components should not rewalk the decl tree
    once per component (was Θ(n²) full loc→decl map materializations).
    """
    n_siblings = 12
    with create_defs_folder_sandbox() as sandbox:
        for i in range(n_siblings):
            sandbox.scaffold_component(
                component_cls=EmptyComponent,
                defs_path=f"comp_{i}",
                defs_yaml_contents={
                    "type": (
                        "dagster_tests.components_tests.component_tree_tests"
                        ".test_component_decl_tree_caching.EmptyComponent"
                    ),
                },
            )

        with sandbox.build_component_tree() as tree:
            original = ComponentTree._component_decl_tree  # noqa: SLF001
            call_count = 0

            def counting_component_decl_tree(self: ComponentTree):
                nonlocal call_count
                call_count += 1
                return original(self)

            with patch.object(
                ComponentTree,
                "_component_decl_tree",
                counting_component_decl_tree,
            ):
                tree.build_defs()

            # One materialization is enough to seed cacheable child decls for
            # the rest of the load. A few more is fine if root / path lookup
            # paths need a second pass; once-per-sibling is not.
            assert call_count < n_siblings, (
                f"_component_decl_tree was called {call_count} times for "
                f"{n_siblings} sibling components (expected O(1) materializations, "
                f"not once per component)"
            )


def test_first_tree_walk_seeds_child_component_decls() -> None:
    """After one tree materialization, filesystem child locs should have
    component_decl cached without needing a second full walk.
    """
    with create_defs_folder_sandbox() as sandbox:
        child_path = sandbox.scaffold_component(
            component_cls=EmptyComponent,
            defs_path="seeded_child",
            defs_yaml_contents={
                "type": (
                    "dagster_tests.components_tests.component_tree_tests"
                    ".test_component_decl_tree_caching.EmptyComponent"
                ),
            },
        )

        with sandbox.build_component_tree() as tree:
            # Materialize the tree once (does not load components).
            tree._component_decl_tree()  # noqa: SLF001

            child_loc = ComponentPath.from_path(child_path)
            # Yaml multi-doc uses instance key 0 for a single document.
            child_instance_loc = ComponentPath.from_path(child_path, instance_key=0)

            cached_folder = tree.state_tracker.get_cache_data(child_loc).component_decl
            cached_instance = tree.state_tracker.get_cache_data(child_instance_loc).component_decl

            assert cached_folder is not None or cached_instance is not None, (
                "Expected first _component_decl_tree() call to seed component_decl "
                "for the child component location"
            )
