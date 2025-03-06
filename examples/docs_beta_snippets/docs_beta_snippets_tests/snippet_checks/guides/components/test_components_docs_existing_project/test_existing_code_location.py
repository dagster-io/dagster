from pathlib import Path

from docs_beta_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
    isolated_snippet_generation_environment,
)
from docs_beta_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    re_ignore_after,
    re_ignore_before,
    run_command_and_snippet_output,
)

COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "existing-project"
)

MY_EXISTING_PROJECT = Path(__file__).parent / "my-existing-project"
MASK_MY_EXISTING_PROJECT = (r"\/.*?\/my-existing-project", "/.../my-existing-project")


def test_components_docs_index(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        _run_command(f"cp -r {MY_EXISTING_PROJECT} . && cd my-existing-project")
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        # Add components section to pyproject.toml
        pyproject_contents = Path("pyproject.toml").read_text()
        tool_dg_section = format_multiline("""
            [tool.dg]
            directory_type = "project"

            [tool.dg.project]
            root_module = "my_existing_project"
            defs_module = "my_existing_project.defs"
        """)
        pyproject_contents = pyproject_contents.replace(
            "[tool.dagster]", f"{tool_dg_section}\n\n[tool.dagster]"
        )
        Path("pyproject.toml").write_text(pyproject_contents)

        check_file(
            "pyproject.toml",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-pyproject.toml",
            snippet_replace_regex=[
                re_ignore_before("[tool.dg]"),
                re_ignore_after('code_location_name = "my_existing_project"'),
            ],
            update_snippets=update_snippets,
        )

        run_command_and_snippet_output(
            cmd="uv venv",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-uv-venv.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )

        run_command_and_snippet_output(
            cmd="uv sync && uv add dagster-components",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-uv-freeze.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )

        _run_command(
            f"uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}'"
        )
        _run_command(
            "uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        run_command_and_snippet_output(
            cmd="mkdir my_existing_project/defs",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-mkdir-defs.txt",
            update_snippets=update_snippets,
        )

        check_file(
            Path("my_existing_project") / "definitions.py",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-initial-definitions.py",
            update_snippets=update_snippets,
        )

        # Update definitions.py to use components
        create_file(
            Path("my_existing_project") / "definitions.py",
            contents=format_multiline("""
                from pathlib import Path

                import dagster_components as dg_components
                import my_existing_project.defs
                from my_existing_project import assets

                import dagster as dg

                all_assets = dg.load_assets_from_modules([assets])

                defs = dg.Definitions.merge(
                    dg.Definitions(assets=all_assets),
                    dg_components.build_component_defs(my_existing_project.defs),
                )
            """),
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-updated-definitions.py",
        )

        _run_command(
            "uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        run_command_and_snippet_output(
            cmd="dg list component-type",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_EXISTING_PROJECT],
        )
