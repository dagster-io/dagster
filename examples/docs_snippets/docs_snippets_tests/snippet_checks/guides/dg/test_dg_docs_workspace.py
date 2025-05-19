from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
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


def test_dg_docs_workspace(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        # Scaffold workspace
        # TODO: Make this use "active" python environment in docs followup

        run_command_and_snippet_output(
            cmd="dg scaffold workspace --use-editable-dagster dagster-workspace && cd dagster-workspace",
            snippet_path=DG_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-scaffold-workspace.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_WORKSPACE,
                (r"\nUsing[\s\S]*", "\n..."),
                (r"\nUsing[\s\S]*", "\n..."),
            ],
            print_cmd="dg scaffold workspace dagster-workspace && cd dagster-workspace",
        )

        run_command_and_snippet_output(
            cmd="dg scaffold project --use-editable-dagster --python-environment uv_managed projects/project-1",
            snippet_path=DG_SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-scaffold-project.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_WORKSPACE,
                (r"\nUsing[\s\S]*", "\n..."),
                (r"\nUsing[\s\S]*", "\n..."),
            ],
            print_cmd="dg scaffold project --python-environment uv_managed projects/project-1",
        )

        # Remove files we don't want to show up in the tree
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(r"find . -type d -name project_1.egg-info -exec rm -r {} \+")

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=DG_SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            # Remove --sort size from tree output, sadly OSX and Linux tree
            # sort differently when using alpha sort
            snippet_replace_regex=[
                (r"\d+ directories, \d+ files", "..."),
            ],
            custom_comparison_fn=compare_tree_output,
        )
        check_file(
            "dg.toml",
            DG_SNIPPETS_DIR / f"{get_next_snip_number()}-dg.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                (r"\[workspace\.scaffold_project_options\]\n", ""),
                (r"use_editable_dagster = true\n", ""),
            ],
        )

        # Validate project toml
        check_file(
            "projects/project-1/pyproject.toml",
            DG_SNIPPETS_DIR / f"{get_next_snip_number()}-project-pyproject.toml",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                re_ignore_before("[tool.dg]"),
                re_ignore_after('root_module = "project_1"'),
            ],
        )

        # Scaffold new project
        run_command_and_snippet_output(
            cmd="dg scaffold project projects/project-2 --python-environment uv_managed --use-editable-dagster",
            snippet_path=DG_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-project.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_MY_WORKSPACE,
                (r"\nUsing[\s\S]*", "\n..."),
            ],
            print_cmd="dg scaffold project projects/project-2 --python-environment uv_managed",
        )

        # List projects
        run_command_and_snippet_output(
            cmd="dg list project",
            snippet_path=DG_SNIPPETS_DIR / f"{get_next_snip_number()}-project-list.txt",
            update_snippets=update_snippets,
        )

        # Create workspace.yaml file
        create_file(
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
            DG_SNIPPETS_DIR / f"{get_next_snip_number()}-workspace.yaml",
        )

        # Ensure dagster loads
        output = _run_command("uv tool run dagster definitions validate")
        assert "Validation successful for code location project_1" in output
        assert "Validation successful for code location project_2" in output
