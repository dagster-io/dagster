from pathlib import Path

from dagster._utils.env import environ
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
    run_command_and_snippet_output,
)

MASK_MY_EXISTING_PROJECT = (r" \/.*?\/my-existing-project", " /.../my-existing-project")


COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "migrating-definitions"
)


MY_EXISTING_PROJECT = Path(__file__).parent / "my-existing-project"


def test_components_docs_migrating_definitions(update_snippets: bool) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        _run_command(f"cp -r {MY_EXISTING_PROJECT} . && cd my-existing-project")
        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )
        _run_command("mkdir -p my_existing_project/defs")

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        check_file(
            Path("my_existing_project") / "definitions.py",
            COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-definitions-before.py",
            update_snippets=update_snippets,
        )

        _run_command(cmd="uv venv")
        _run_command(cmd="uv sync")
        _run_command(
            f"uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}'"
        )

        run_command_and_snippet_output(
            cmd="dg scaffold component 'dagster_components.dagster.DefinitionsComponent' elt-definitions",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_EXISTING_PROJECT],
        )

        run_command_and_snippet_output(
            cmd="mv my_existing_project/elt/* my_existing_project/defs/elt-definitions",
            snippet_path=COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-mv.txt",
            update_snippets=update_snippets,
        )
        _run_command("rm -rf my_existing_project/elt")

        create_file(
            Path("my_existing_project") / "defs" / "elt-definitions" / "definitions.py",
            format_multiline("""
                import dagster as dg

                from . import assets
                from .jobs import sync_tables_daily_schedule, sync_tables_job

                defs = dg.Definitions(
                    assets=dg.load_assets_from_modules([assets]),
                    jobs=[sync_tables_job],
                    schedules=[sync_tables_daily_schedule],
                )
            """),
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-elt-nested-definitions.py",
        )

        create_file(
            Path("my_existing_project") / "defs" / "elt-definitions" / "component.yaml",
            format_multiline("""
            type: dagster_components.dagster.DefinitionsComponent

            attributes:
              definitions_path: definitions.py
            """),
            COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-component-yaml.txt",
        )

        create_file(
            Path("my_existing_project") / "definitions.py",
            format_multiline("""
            from pathlib import Path

            import dagster_components as dg_components
            from my_existing_project import defs as component_defs
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
                dg_components.build_component_defs(component_defs),
            )
        """),
            COMPONENTS_SNIPPETS_DIR / f"{get_next_snip_number()}-definitions-after.py",
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )

        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-tree-after.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        # validate loads
        _run_command(
            "uv pip freeze && uv run dagster asset materialize --select '*' -m 'my_existing_project.definitions'"
        )

        # migrate analytics
        _run_command(
            cmd="dg scaffold component 'dagster_components.dagster.DefinitionsComponent' analytics-definitions",
        )
        _run_command(
            cmd="mv my_existing_project/analytics/* my_existing_project/defs/analytics-definitions && rm -rf my_existing_project/analytics",
        )
        create_file(
            Path("my_existing_project")
            / "defs"
            / "analytics-definitions"
            / "definitions.py",
            format_multiline("""
                import dagster as dg

                from . import assets
                from .jobs import regenerate_analytics_hourly_schedule, regenerate_analytics_job

                defs = dg.Definitions(
                    assets=dg.load_assets_from_modules([assets]),
                    jobs=[regenerate_analytics_job],
                    schedules=[regenerate_analytics_hourly_schedule],
                )
            """),
        )
        create_file(
            Path("my_existing_project")
            / "defs"
            / "analytics-definitions"
            / "component.yaml",
            format_multiline("""
                type: dagster_components.dagster.DefinitionsComponent

                attributes:
                  definitions_path: definitions.py
            """),
        )

        _run_command(r"find . -type d -name __pycache__ -exec rm -r {} \+")
        _run_command(
            r"find . -type d -name my_existing_project.egg-info -exec rm -r {} \+"
        )
        run_command_and_snippet_output(
            cmd="tree",
            snippet_path=COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-tree-after-all.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        create_file(
            Path("my_existing_project") / "definitions.py",
            format_multiline("""
                from pathlib import Path

                import dagster_components as dg_components
                from my_existing_project import defs as component_defs

                defs = dg_components.build_component_defs(component_defs)
            """),
            COMPONENTS_SNIPPETS_DIR
            / f"{get_next_snip_number()}-definitions-after-all.py",
        )
