from pathlib import Path

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
    ) as context:
        _run_command(f"cp -r {MY_EXISTING_PROJECT} . && cd my-existing-project")

        context.run_tree_command_and_snippet_output(
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
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
            import my_existing_project.defs
            from my_existing_project.analytics import assets as analytics_assets
            from my_existing_project.analytics.jobs import (
                regenerate_analytics_hourly_schedule,
                regenerate_analytics_job,
            )

            import dagster as dg
            import dagster.components

            defs = dg.Definitions.merge(
                dg.Definitions(
                    assets=dg.load_assets_from_modules([analytics_assets]),
                    jobs=[regenerate_analytics_job],
                    schedules=[regenerate_analytics_hourly_schedule],
                ),
                dagster.components.load_defs(my_existing_project.defs),
            )
        """),
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-definitions-after.py",
        )

        context.run_tree_command_and_snippet_output(
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-tree-after.txt",
        )

        # validate loads
        _run_command(
            "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        # migrate analytics
        _run_command("mkdir -p my_existing_project/defs/analytics")
        _run_command(
            cmd="mv my_existing_project/analytics/* my_existing_project/defs/analytics && rm -rf my_existing_project/analytics",
        )

        context.run_tree_command_and_snippet_output(
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-tree-after-all.txt",
        )

        context.create_file(
            Path("my_existing_project") / "definitions.py",
            format_multiline("""
                import dagster as dg
                import my_existing_project.defs

                defs = dg.components.load_defs(my_existing_project.defs)
            """),
            SNIPPETS_DIR / f"{context.get_next_snip_number()}-definitions-after-all.py",
        )

        # validate loads
        _run_command(
            "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs-after-all.txt",
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )
