from dagster._utils.env import environ
from docs_beta_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
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
    / "workspace"
)
MASK_MY_WORKSPACE = (r"\/.*?\/dagster-workspace", "/.../dagster-workspace")


def test_components_docs_workspace(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        # Scaffold workspace
        run_command_and_snippet_output(
            cmd='echo "\nproject-1\n" | dg init --use-editable-dagster',
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-init.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_WORKSPACE,
                (r"\nUsing[\s\S]*", "\n..."),
                (r"\nUsing[\s\S]*", "\n..."),
                (
                    r"\(or press Enter to continue without creating a project\): ",
                    "(or press Enter to continue without creating a project): project-1\n",
                ),
                (
                    r"\[dagster-workspace\]: ",
                    "[dagster-workspace]: \n",  # add newline
                ),
            ],
            print_cmd="dg init",
        )

        # Remove files we don't want to show up in the tree
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name project_1.egg-info -exec rm -r {} \+")

        run_command_and_snippet_output(
            cmd="cd dagster-workspace && tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            # Remove --sort size from tree output, sadly OSX and Linux tree
            # sort differently when using alpha sort
            snippet_replace_regex=[
                (r"\d+ directories, \d+ files", "..."),
            ],
            custom_comparison_fn=compare_tree_output,
        )
        check_file(
            "pyproject.toml",
            COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[tool.dagster]"),
                re_ignore_after("is_project = true"),
            ],
        )

        # Validate project toml
        check_file(
            "projects/project-1/pyproject.toml",
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-project-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[tool.dg]"),
                re_ignore_after('root_module = "project_1"'),
            ],
        )

        # Check component types
        run_command_and_snippet_output(
            cmd="cd projects/project-1 && dg list component-type",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-component-type-list.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_WORKSPACE],
        )
        _run_command(
            f"uv add sling_mac_arm64 && uv add --editable '{EDITABLE_DIR / 'dagster-sling'!s}' && uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}[sling]'"
        )
        run_command_and_snippet_output(
            cmd="dg list component-type",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-component-type-list.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_WORKSPACE],
        )

        # Scaffold new project
        run_command_and_snippet_output(
            cmd="cd ../.. && dg scaffold project projects/project-2 --use-editable-dagster",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-project.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_WORKSPACE,
                (r"\nUsing[\s\S]*", "\n..."),
            ],
        )

        # List projects
        run_command_and_snippet_output(
            cmd="dg list project",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-project-list.txt",
            update_snippets=update_snippets,
        )

        # Check component types in new project
        run_command_and_snippet_output(
            cmd="cd projects/project-2 && dg list component-type",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-component-type-list.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_WORKSPACE],
        )

        # Create workspace.yaml file
        _run_command("cd ../../")
        create_file(
            "workspace.yaml",
            format_multiline("""
                load_from:
                  - python_file:
                      relative_path: projects/project-1/project_1/definitions.py
                      location_name: project_1
                      executable_path: projects/project-1/.venv/bin/python
                  - python_file:
                      relative_path: projects/project-2/project_2/definitions.py
                      location_name: project_2
                      executable_path: projects/project-2/.venv/bin/python
            """),
            COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-workspace.yaml",
        )

        # Ensure dagster loads
        output = _run_command("uv tool run dagster definitions validate")
        assert "Validation successful for code location project_1" in output
        assert "Validation successful for code location project_2" in output
