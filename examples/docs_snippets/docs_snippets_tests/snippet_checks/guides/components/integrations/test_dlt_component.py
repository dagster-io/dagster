import textwrap
from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
)
from docs_snippets_tests.snippet_checks.utils import (
    compare_tree_output,
    isolated_snippet_generation_environment,
)

MASK_MY_PROJECT = (r" \/.*?\/my-project", " /.../my-project")
MASK_VENV = (r"Using.*\.venv.*", "")
MASK_USING_LOG_MESSAGE = (r"Using.*\n", "")

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


def test_components_docs_adding_attributes_to_assets(
    update_snippets: bool, update_screenshots: bool, get_selenium_driver
) -> None:
    with (
        isolated_snippet_generation_environment(
            should_update_snippets=update_snippets,
            snapshot_base_dir=SNIPPETS_DIR,
            global_snippet_replace_regexes=[
                MASK_MY_PROJECT,
                MASK_VENV,
                MASK_USING_LOG_MESSAGE,
            ],
        ) as context,
        environ({"SOURCES__GITHUB__ACCESS_TOKEN": "XX"}),
    ):
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="dg scaffold project my-project --python-environment uv_managed --use-editable-dagster && cd my-project/src",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--python-environment uv_managed --use-editable-dagster ", ""),
                ("--editable.*dagster-sling", "dagster-sling"),
            ],
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-dlt'}",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-add-dlt.txt",
            print_cmd="uv add dagster-dlt",
            ignore_output=True,
        )

        # scaffold dlt component
        context.run_command_and_snippet_output(
            cmd="dg scaffold dagster_dlt.DltLoadCollectionComponent github_snowflake_ingest \\\n  --source github --destination snowflake",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-dlt-component.txt",
        )

        # Tree the project
        context.run_tree_command_and_snippet_output(
            tree_path="my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
        )

        context.check_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "loads.py",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-loads.py",
        )

        context.check_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "component.yaml",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-component.yaml",
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
            Path("my_project") / "defs" / "github_snowflake_ingest" / "component.yaml",
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
            / f"{context.get_next_snip_number()}-customized-component.yaml",
        )
        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )
        # Update component.yaml
        context.create_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "component.yaml",
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
            / f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml
        context.create_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "component.yaml",
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
            / f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # List defs
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )
