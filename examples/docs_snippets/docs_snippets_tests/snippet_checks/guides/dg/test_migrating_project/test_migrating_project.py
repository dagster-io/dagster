import textwrap
from contextlib import ExitStack
from pathlib import Path

import pytest
from dagster_dg.cli.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.test_components_docs import (
    DgTestPackageManager,
)
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_PLUGIN_CACHE_REBUILD,
    format_multiline,
    get_editable_install_cmd_for_dg,
    get_editable_install_cmd_for_project,
    insert_before_matching_line,
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
            f"cp -r {project_root} my-existing-project && cd my-existing-project"
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
                cmd=f"uv venv && {get_editable_install_cmd_for_project(Path('.'), package_manager)}",
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

        if package_manager == "uv":
            # We're using a local `dg` install in reality to avoid polluting global env but we'll fake the global one
            run_command_and_snippet_output(
                cmd=get_editable_install_cmd_for_dg(package_manager),
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-install-dg.txt",
                update_snippets=update_snippets,
                ignore_output=True,
                print_cmd="uv tool install dagster-dg",
            )
        elif package_manager == "pip":
            run_command_and_snippet_output(
                cmd=get_editable_install_cmd_for_dg(package_manager),
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-install-dg.txt",
                update_snippets=update_snippets,
                ignore_output=True,
                print_cmd="pip install dagster-dg",
            )

        # Delete egg-info from editable install
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )

        # Add entry point to package metadata
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

        # Create my_existing_project.components
        run_command_and_snippet_output(
            cmd="mkdir my_existing_project/components && touch my_existing_project/components/__init__.py",
            snippet_path=_SNIPPETS_DIR / f"{get_next_snip_number()}-create-lib.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_USING_LOG_MESSAGE],
        )

        # Add dagster_dg.plugin to pyproject.toml
        if package_manager == "uv":
            pyproject_toml_content = Path("pyproject.toml").read_text()
            pyproject_toml_content = insert_before_matching_line(
                pyproject_toml_content,
                "\n"
                + format_multiline("""
                    [project.entry-points]
                    "dagster_dg.plugin" = { my_existing_project = "my_existing_project.components"}
                """),
                r"\[build-system\]",
            )
            Path("pyproject.toml").write_text(pyproject_toml_content)
            check_file(
                "pyproject.toml",
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-plugin-config.toml",
                update_snippets=update_snippets,
                snippet_replace_regex=[
                    re_ignore_before(r"[project.entry-points]"),
                    (r"\[build-system\][\s\S]*", "..."),
                ],
            )
            run_command_and_snippet_output(
                cmd="uv pip install --editable .",
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-reinstall-package.txt",
                update_snippets=update_snippets,
                ignore_output=True,
            )

        elif package_manager == "pip":
            setup_cfg_content = format_multiline("""
                [options.entry_points]
                dagster_dg.plugin =
                    my_existing_project = my_existing_project.components
            """)
            Path("setup.cfg").write_text(setup_cfg_content)
            check_file(
                "setup.cfg",
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-plugin-config.txt",
                update_snippets=update_snippets,
            )
            run_command_and_snippet_output(
                cmd="pip install --editable .",
                snippet_path=_SNIPPETS_DIR
                / f"{get_next_snip_number()}-{package_manager}-reinstall-package.txt",
                update_snippets=update_snippets,
                ignore_output=True,
            )

        run_command_and_snippet_output(
            cmd="dg scaffold component-type Foo",
            snippet_path=_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-component-type.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_USING_LOG_MESSAGE,
                MASK_MY_EXISTING_PROJECT,
                MASK_PLUGIN_CACHE_REBUILD,
            ],
        )

        plugin_table = run_command_and_snippet_output(
            cmd="dg list plugins",
            snippet_path=_SNIPPETS_DIR / f"{get_next_snip_number()}-list-plugins.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_USING_LOG_MESSAGE,
                MASK_PLUGIN_CACHE_REBUILD,
            ],
        )
        assert "my_existing_project.components.Foo" in plugin_table

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
            Path("my_existing_project") / "defs" / "__init__.py",
            contents="",
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
