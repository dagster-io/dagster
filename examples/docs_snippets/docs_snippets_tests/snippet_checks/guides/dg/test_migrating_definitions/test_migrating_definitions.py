from pathlib import Path

from dagster_dg_core.utils import activate_venv

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    format_multiline,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
)

MASK_MY_EXISTING_PROJECT = (r" \/.*?\/my-existing-project", " /.../my-existing-project")
MASK_ISORT = (r"#isort:skip-file", "# definitions.py")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")
MASK_PKG_RESOURCES = (r"\n.*import pkg_resources\n", "")
MASK_REQUESTS_WARNING = (
    r"[^\n]*RequestsDependencyWarning[^\n]*\n\s*warnings\.warn\(\n",
    "",
)


SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "migrating-definitions"
)


MY_EXISTING_PROJECT = Path(__file__).parent / "my-existing-project"


def test_components_docs_migrating_definitions(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment(
        should_update_snippets=update_snippets,
        snapshot_base_dir=SNIPPETS_DIR,
        global_snippet_replace_regexes=[MASK_PKG_RESOURCES],
    ) as context:
        _run_command(f"cp -r {MY_EXISTING_PROJECT} . && cd my-existing-project")
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )

        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_existing_project") / "definitions.py",
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-definitions-before.py",
            snippet_replace_regex=[MASK_ISORT],
        )

        _run_command(cmd="uv venv")
        _run_command(
            f"uv add --editable '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'libraries' / 'dagster-shared'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'dagster-pipes'!s}' "
            f"'{DAGSTER_ROOT / 'python_modules' / 'dagster-graphql'!s}'"
        )

        _run_command("mkdir -p my_existing_project/defs/elt")
        context.run_command_and_snippet_output(
            cmd="mv my_existing_project/elt/* my_existing_project/defs/elt",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-mv.txt",
        )
        _run_command("rm -rf my_existing_project/elt")

        context.create_file(
            Path("my_existing_project") / "definitions.py",
            format_multiline("""
            from pathlib import Path

            from my_existing_project.analytics import assets as analytics_assets
            from my_existing_project.analytics.jobs import (
                regenerate_analytics_hourly_schedule,
                regenerate_analytics_job,
            )

            import dagster as dg

            defs = dg.Definitions.merge(
                dg.Definitions(
                    assets=dg.load_assets_from_modules([analytics_assets]),
                    jobs=[regenerate_analytics_job],
                    schedules=[regenerate_analytics_hourly_schedule],
                ),
                dg.load_from_defs_folder(project_root=Path(__file__).parent.parent),
            )
        """),
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-definitions-after.py",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )

        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-tree-after.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # validate loads
        if not update_snippets:
            _run_command(
                "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
            )

        # migrate analytics
        _run_command("mkdir -p my_existing_project/defs/analytics")
        _run_command(
            cmd="mv my_existing_project/analytics/* my_existing_project/defs/analytics && rm -rf my_existing_project/analytics",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )
        context.run_command_and_snippet_output(
            cmd="tree",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-tree-after-all.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.create_file(
            Path("my_existing_project") / "definitions.py",
            format_multiline("""
                from pathlib import Path
                import dagster as dg

                defs = dg.load_from_defs_folder(project_root=Path(__file__).parent.parent)
            """),
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-definitions-after-all.py",
        )

        # validate loads
        if not update_snippets:
            _run_command(
                "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
            )

        with activate_venv(".venv"):
            context.run_command_and_snippet_output(
                cmd="dg list defs",
                snippet_path=SNIPPETS_DIR
                / f"{context.get_next_snip_number()}-list-defs-after-all.txt",
                snippet_replace_regex=[
                    MASK_VENV,
                    MASK_USING_LOG_MESSAGE,
                    MASK_REQUESTS_WARNING,
                ],
            )
