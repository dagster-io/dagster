from pathlib import Path

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
    re_ignore_after,
    re_ignore_before,
)

_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "creating-dg-plugin"
)

_MY_LIBRARY = Path(__file__).parent / "my-library"
_MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")


def test_creating_dg_plugin(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets,
        snapshot_base_dir=_SNIPPETS_DIR,
    ) as context:
        _run_command(f"cp -r {_MY_LIBRARY} . && cd my-library")

        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.create_file(
            Path("src") / "my_library" / "empty_component.py",
            snippet_path=f"{context.get_next_snip_number()}-empty-component.py",
            contents=format_multiline("""
            from dataclasses import dataclass

            import dagster as dg


            @dataclass
            class EmptyComponent(dg.Component, dg.Resolvable):
                \"\"\"A component that does nothing.\"\"\"

                def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                    return dg.Definitions()
            """),
        )

        # Add entry point to pyproject.toml
        pyproject_toml_path = Path("pyproject.toml")
        pyproject_toml_content = pyproject_toml_path.read_text()
        pyproject_toml_content += format_multiline("""
            [project.entry-points]
            "dagster_dg_cli.registry_modules" = { my_library = "my_library" }
        """)
        pyproject_toml_path.write_text(pyproject_toml_content)

        context.check_file(
            "pyproject.toml",
            snippet_path=f"{context.get_next_snip_number()}-pyproject.toml",
            snippet_replace_regex=[
                re_ignore_before("[project.entry-points]"),
            ],
        )

        # Add import statement to my_library/__init__.py
        init_py_path = Path("src") / "my_library" / "__init__.py"
        init_py_content = init_py_path.read_text().strip()
        init_py_content += format_multiline("""
            from my_library.empty_component import EmptyComponent
        """).strip()
        init_py_path.write_text(init_py_content)

        context.check_file(
            init_py_path,
            snippet_path=f"{context.get_next_snip_number()}-init.py",
        )

        # Create a virtual environment, install the package, and list components
        _run_command("uv venv .venv")
        _run_command(
            f"uv pip install --editable . "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-shared'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster-pipes'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-dg-core'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-dg-cli'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-cloud-cli'!s}' "
            f"--editable '{DAGSTER_ROOT / 'python_modules' / 'dagster-graphql'!s}'"
        )

        context.run_command_and_snippet_output(
            cmd="source .venv/bin/activate && dg list components --package my_library",
            snippet_path=f"{context.get_next_snip_number()}-list-components.txt",
            print_cmd="dg list components --package my_library",
            snippet_replace_regex=[_MASK_USING_LOG_MESSAGE],
        )
