import tempfile
import textwrap
from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    compare_tree_output,
    isolated_snippet_generation_environment,
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")
MASK_PKG_RESOURCES = (r"\n.*import pkg_resources\n", "")

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "integrations"
    / "dlt-component"
)


def test_dlt_components_docs_adding_attributes_to_assets(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
) -> None:
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_MY_PROJECT,
                    MASK_VENV,
                    MASK_USING_LOG_MESSAGE,
                    MASK_PKG_RESOURCES,
                ],
            )
        )
        tmp_dir = stack.enter_context(tempfile.TemporaryDirectory())
        stack.enter_context(
            environ(
                {"SOURCES__GITHUB__ACCESS_TOKEN": "XX", "DLT_CONFIG_FOLDER": tmp_dir}
            )
        )
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                (
                    "--uv-sync --use-editable-dagster ",
                    "",
                ),
                ("--editable.*dagster-sling", "dagster-sling"),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )
        stack.enter_context(activate_venv("../.venv"))

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-dlt'}",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-add-dlt.txt",
            print_cmd="uv add dagster-dlt",
            ignore_output=True,
        )

        # scaffold dlt component
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_dlt.DltLoadCollectionComponent github_snowflake_ingest \\\n  --source github --destination snowflake",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-dlt-component.txt",
            ignore_output=True,
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "loads.py",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-loads.py",
        )

        context.check_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "defs.yaml",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-defs.yaml",
        )

        # Update loads.py
        context.create_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "loads.py",
            contents=textwrap.dedent(
                """\
                import dlt
                from .github import github_reactions, github_repo_events, github_stargazers

                dlthub_dlt_stargazers_source = github_stargazers("dlt-hub", "dlt")
                dlthub_dlt_stargazers_pipeline = dlt.pipeline(
                    "github_stargazers", destination="snowflake", dataset_name="dlthub_stargazers"
                )
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-customized-loads.py",
        )

        # Update component.yaml
        context.create_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_dlt.DltLoadCollectionComponent

                attributes:
                  loads:
                    - source: .loads.dlthub_dlt_stargazers_source
                      pipeline: .loads.dlthub_dlt_stargazers_pipeline
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-customized-defs.yaml",
        )
        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )
        # Update component.yaml
        context.create_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_dlt.DltLoadCollectionComponent

                attributes:
                  loads:
                    - source: .loads.dlthub_dlt_stargazers_source
                      pipeline: .loads.dlthub_dlt_stargazers_pipeline
                      translation:
                        group_name: github_data
                        description: "Loads all users who have starred the dlt-hub/dlt repo"
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-customized-defs.yaml",
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml
        context.create_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_dlt.DltLoadCollectionComponent

                attributes:
                  loads:
                    - source: .loads.dlthub_dlt_stargazers_source
                      pipeline: .loads.dlthub_dlt_stargazers_pipeline
                      translation:
                        metadata:
                          resource_name: "{{ resource.name }}"
                          pipeline_name: "{{ pipeline.pipeline_name }}"
                          is_transformer: "{{ resource.is_transformer }}"
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-customized-defs.yaml",
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )


def test_dlt_components_basic_scaffold() -> None:
    # Added to test odd edge case where scaffolding & loading defs in a bare env failed
    # https://github.com/dagster-io/dagster/pull/30905
    # Does not power docs, but easiest to test this using the docs snippets utilities
    with ExitStack() as stack:
        stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=False,
                snapshot_base_dir=SNIPPETS_DIR,
            )
        )
        tmp_dir = stack.enter_context(tempfile.TemporaryDirectory())
        stack.enter_context(
            environ(
                {"SOURCES__GITHUB__ACCESS_TOKEN": "XX", "DLT_CONFIG_FOLDER": tmp_dir}
            )
        )
        _run_command(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src"
        )
        stack.enter_context(activate_venv("../.venv"))
        _run_command(cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-dlt'}")
        _run_command(
            cmd="dg scaffold defs dagster_dlt.DltLoadCollectionComponent github_snowflake_ingest"
        )

        _run_command(cmd="dg list defs")
