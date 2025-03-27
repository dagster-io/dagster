from pathlib import Path

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
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
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "migrating-project"
)

MY_EXISTING_PROJECT = Path(__file__).parent / "my-existing-project"
MASK_MY_EXISTING_PROJECT = (r"\/.*?\/my-existing-project", "/.../my-existing-project")
MASK_ISORT = (r"#isort:skip-file", "# definitions.py")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")


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

        # Inject dagster-components as a dependency
        setup_py_content = Path("setup.py").read_text()
        setup_py_content = setup_py_content.replace(
            '"dagster",\n', '"dagster",\n        "dagster-components",\n'
        )
        Path("setup.py").write_text(setup_py_content)

        # In the tests we use `uv` to avoid need to activate a virtual env, in the
        _run_command("uv venv .venv")
        _run_command("uv pip install -e .")

        check_file(
            "setup.py",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-setup.py",
            snippet_replace_regex=[
                re_ignore_before("[tool.dg]"),
                re_ignore_after('code_location_name = "my_existing_project"'),
            ],
            update_snippets=update_snippets,
        )

        _run_command(
            f"uv pip install --editable '{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-components'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-shared'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster-pipes'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster-graphql'!s}'"
        )
        _run_command(
            ".venv/bin/dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        # Add components section to pyproject.toml
        pyproject_toml_content = format_multiline("""
            [tool.dg]
            directory_type = "project"

            [tool.dg.project]
            root_module = "my_existing_project"
            code_location_target_module = "my_existing_project.definitions"
        """)
        Path("pyproject.toml").write_text(pyproject_toml_content)

        check_file(
            "pyproject.toml",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-pyproject.toml",
            update_snippets=update_snippets,
        )

        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_USING_LOG_MESSAGE],
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
            snippet_replace_regex=[MASK_ISORT],
        )

        # Update definitions.py to use components
        create_file(
            Path("my_existing_project") / "definitions.py",
            contents=format_multiline("""
                import dagster_components as dg_components
                import my_existing_project.defs
                from my_existing_project.assets import my_asset

                import dagster as dg

                defs = dg.Definitions.merge(
                    dg.Definitions(assets=[my_asset]),
                    dg_components.load_defs(my_existing_project.defs),
                )
            """),
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-updated-definitions.py",
        )

        create_file(
            Path("my_existing_project") / "defs" / "autoloaded_asset.py",
            contents=format_multiline("""
                import dagster as dg


                @dg.asset
                def autoloaded_asset(): ...
            """),
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-autoloaded-asset.py",
        )

        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_USING_LOG_MESSAGE],
        )
