from contextlib import ExitStack
from pathlib import Path

import pytest

from dagster._utils.env import activate_venv
from docs_snippets_tests.snippet_checks.guides.components.test_components_docs import (
    DgTestPackageManager,
)
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
    get_editable_install_cmd_for_dg,
    get_editable_install_cmd_for_project,
    isolated_snippet_generation_environment,
    make_letter_iterator,
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

_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "migrating-project"
)

MASK_MY_EXISTING_PROJECT = (r"\/.*?\/my-existing-project", "/.../my-existing-project")
MASK_ISORT = (r"#isort:skip-file", "# definitions.py")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")


@pytest.mark.parametrize("package_manager", ["uv", "pip"])
def test_migrating_project(
    update_snippets: bool, package_manager: DgTestPackageManager
) -> None:
    with ExitStack() as context_stack:
        get_next_snip_number = context_stack.enter_context(
            isolated_snippet_generation_environment()
        )

        project_root = Path(__file__).parent / f"my-existing-project-{package_manager}"
        _run_command(
            f"cp -r {project_root} . && cd my-existing-project-{package_manager}"
        )
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=_SNIPPETS_DIR
            / f"{get_next_snip_number()}-{package_manager}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        venv_snip_no = get_next_snip_number()
        get_letter = make_letter_iterator()
        get_venv_snip_path = (
            lambda: _SNIPPETS_DIR
            / f"{venv_snip_no}-{get_letter()}-{package_manager}-venv.txt"
        )
        if package_manager == "uv":
            run_command_and_snippet_output(
                cmd=get_editable_install_cmd_for_project(Path("."), package_manager),
                snippet_path=get_venv_snip_path(),
                update_snippets=update_snippets,
                print_cmd="uv sync",
                ignore_output=True,
            )
            run_command_and_snippet_output(
                cmd="source .venv/bin/activate",
                snippet_path=get_venv_snip_path(),
                update_snippets=update_snippets,
                ignore_output=True,
            )
            # Required to actually activate venv for snippet generation purposes
            context_stack.enter_context(activate_venv(".venv"))
        elif package_manager == "pip":
            run_command_and_snippet_output(
                cmd="python -m venv .venv",
                snippet_path=get_venv_snip_path(),
                update_snippets=update_snippets,
                ignore_output=True,
            )
            run_command_and_snippet_output(
                cmd="source .venv/bin/activate",
                snippet_path=get_venv_snip_path(),
                update_snippets=update_snippets,
                ignore_output=True,
            )
            # Required to actually activate venv for snippet generation purposes
            context_stack.enter_context(activate_venv(".venv"))
            run_command_and_snippet_output(
                cmd=get_editable_install_cmd_for_project(Path("."), package_manager),
                snippet_path=get_venv_snip_path(),
                update_snippets=update_snippets,
                print_cmd="pip install --editable .",
                ignore_output=True,
            )

        # Test to make sure everything is working
        _run_command(
            "dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        # Add components section to pyproject.toml
        if package_manager == "uv":
            pyproject_toml_content = Path("pyproject.toml").read_text()
            pyproject_toml_content = (
                pyproject_toml_content
                + "\n"
                + format_multiline("""
                [tool.dg]
                directory_type = "project"

                [tool.dg.project]
                root_module = "my_existing_project"
                code_location_target_module = "my_existing_project.definitions"
            """)
            )
            Path("pyproject.toml").write_text(pyproject_toml_content)
            check_file(
                "pyproject.toml",
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-config.toml",
                update_snippets=update_snippets,
                snippet_replace_regex=[re_ignore_before(r"[tool.dg]")],
            )

        elif package_manager == "pip":
            Path("dg.toml").write_text(
                format_multiline("""
                    directory_type = "project"

                    [project]
                    root_module = "my_existing_project"
                    code_location_target_module = "my_existing_project.definitions"
                """)
            )
            check_file(
                "dg.toml",
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-config.toml",
                update_snippets=update_snippets,
            )

        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=_SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_USING_LOG_MESSAGE],
        )

        run_command_and_snippet_output(
            cmd="mkdir my_existing_project/defs",
            snippet_path=_SNIPPETS_DIR / f"{get_next_snip_number()}-mkdir-defs.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )

        check_file(
            Path("my_existing_project") / "definitions.py",
            snippet_path=_SNIPPETS_DIR
            / f"{get_next_snip_number()}-initial-definitions.py",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_ISORT],
        )

        # Update definitions.py to use components
        create_file(
            Path("my_existing_project") / "definitions.py",
            contents=format_multiline("""
                import my_existing_project.defs
                from my_existing_project.assets import my_asset

                import dagster as dg

                defs = dg.Definitions.merge(
                    dg.Definitions(assets=[my_asset]),
                    dg.components.load_defs(my_existing_project.defs),
                )
            """),
            snippet_path=_SNIPPETS_DIR
            / f"{get_next_snip_number()}-updated-definitions.py",
        )

        create_file(
            Path("my_existing_project") / "defs" / "autoloaded_asset.py",
            contents=format_multiline("""
                import dagster as dg


                @dg.asset
                def autoloaded_asset(): ...
            """),
            snippet_path=_SNIPPETS_DIR
            / f"{get_next_snip_number()}-autoloaded-asset.py",
        )

        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=_SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_USING_LOG_MESSAGE],
        )
