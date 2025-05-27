from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
    format_multiline,
)
from docs_snippets_tests.snippet_checks.utils import (
    compare_tree_output,
    isolated_snippet_generation_environment,
    re_ignore_after,
    re_ignore_before,
)

DG_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "workspace"
)
MASK_MY_WORKSPACE = (r"\/.*?\/dagster-workspace", "/.../dagster-workspace")
MASK_USING_LOG_MESSAGE = (r"\nUsing[\s\S]*", "\n...")


def test_dg_docs_workspace(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets,
        snapshot_base_dir=DG_SNIPPETS_DIR,
        global_snippet_replace_regexes=[
            MASK_EDITABLE_DAGSTER,
            MASK_MY_WORKSPACE,
            MASK_USING_LOG_MESSAGE,
        ],
    ) as context:
        # Scaffold workspace
        # TODO: Make this use "active" python environment in docs followup

        context.run_command_and_snippet_output(
            cmd="dg scaffold workspace --use-editable-dagster dagster-workspace && cd dagster-workspace",
            snippet_path=f"{context.get_next_snip_number()}-dg-scaffold-workspace.txt",
            print_cmd="dg scaffold workspace dagster-workspace && cd dagster-workspace",
        )

        context.run_command_and_snippet_output(
            cmd="dg scaffold project --use-editable-dagster --python-environment uv_managed projects/project-1",
            snippet_path=f"{context.get_next_snip_number()}-dg-scaffold-project.txt",
            print_cmd="dg scaffold project --python-environment uv_managed projects/project-1",
        )

        # Remove files we don't want to show up in the tree
        context._run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        context._run_command(
            r"find . -type d -name project_1.egg-info -exec rm -r {} \+"
        )

        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            # Remove --sort size from tree output, sadly OSX and Linux tree
            # sort differently when using alpha sort
            snippet_replace_regex=[
                (r"\d+ directories, \d+ files", "..."),
            ],
            custom_comparison_fn=compare_tree_output,
        )
        context.check_file(
            "dg.toml",
            DG_SNIPPETS_DIR / f"{context.get_next_snip_number()}-dg.toml",
            snippet_replace_regex=[
                (r"\[workspace\.scaffold_project_options\]\n", ""),
                (r"use_editable_dagster = true\n", ""),
            ],
        )

        # Validate project toml
        context.check_file(
            "projects/project-1/pyproject.toml",
            DG_SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-project-pyproject.toml",
            snippet_replace_regex=[
                re_ignore_before("[tool.dg]"),
                re_ignore_after('root_module = "project_1"'),
            ],
        )

        # Scaffold new project
        context.run_command_and_snippet_output(
            cmd="dg scaffold project projects/project-2 --python-environment uv_managed --use-editable-dagster",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            print_cmd="dg scaffold project projects/project-2 --python-environment uv_managed",
        )

        # List projects
        context.run_command_and_snippet_output(
            cmd="dg list project",
            snippet_path=f"{context.get_next_snip_number()}-project-list.txt",
        )

        # Create workspace.yaml file
        context.create_file(
            "workspace.yaml",
            format_multiline("""
                load_from:
                  - python_file:
                      relative_path: projects/project-1/src/project_1/definitions.py
                      location_name: project_1
                      executable_path: projects/project-1/.venv/bin/python
                  - python_file:
                      relative_path: projects/project-2/src/project_2/definitions.py
                      location_name: project_2
                      executable_path: projects/project-2/.venv/bin/python
            """),
            DG_SNIPPETS_DIR / f"{context.get_next_snip_number()}-workspace.yaml",
        )

        # Ensure dagster loads
        output = context._run_command("uv tool run dagster definitions validate")
        assert "Validation successful for code location project_1" in output
        assert "Validation successful for code location project_2" in output
