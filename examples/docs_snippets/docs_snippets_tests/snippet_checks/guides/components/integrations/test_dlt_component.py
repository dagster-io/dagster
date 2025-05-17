import textwrap
from pathlib import Path

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
    check_file,
    compare_tree_output,
    create_file,
    run_command_and_snippet_output,
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
        isolated_snippet_generation_environment() as get_next_snip_number,
        environ({"SOURCES__GITHUB__ACCESS_TOKEN": "XX"}),
    ):
        # Scaffold code location
        run_command_and_snippet_output(
            cmd="dg scaffold project my-project --python-environment uv_managed --use-editable-dagster && cd my-project/src",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--python-environment uv_managed --use-editable-dagster ", ""),
                ("--editable.*dagster-sling", "dagster-sling"),
            ],
            update_snippets=update_snippets,
            ignore_output=True,
        )

        run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-dlt'}",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-add-dlt.txt",
            update_snippets=update_snippets,
            print_cmd="uv add dagster-dlt",
            ignore_output=True,
        )

        # scaffold dlt component
        run_command_and_snippet_output(
            cmd="dg scaffold dagster_dlt.DltLoadCollectionComponent github_snowflake_ingest \\\n  --source github --destination snowflake",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-scaffold-dlt-component.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_MY_PROJECT],
        )

        # Tree the project
        run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-tree.txt",
            update_snippets=update_snippets,
            custom_comparison_fn=compare_tree_output,
        )

        check_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "loads.py",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-loads.py",
            update_snippets=update_snippets,
        )

        check_file(
            Path("my_project") / "defs" / "github_snowflake_ingest" / "defs.yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-defs.yaml",
            update_snippets=update_snippets,
        )

        # List defs
        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )

        # Update defs.yaml
        create_file(
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
            / f"{get_next_snip_number()}-customized-defs.yaml",
        )

        # List defs
        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )

        # Update defs.yaml
        create_file(
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
            / f"{get_next_snip_number()}-customized-defs.yaml",
        )

        # List defs
        run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-list-defs.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_VENV, MASK_USING_LOG_MESSAGE],
        )
