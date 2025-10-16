import shutil
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
    / "tableau-component"
)


def _swap_to_mock_tableau_component(path: Path) -> None:
    path.write_text(
        path.read_text().replace(
            "dagster_tableau.TableauComponent",
            "my_project.defs.tableau_ingest.test_tableau_utils.MockTableauComponent",
        )
    )


def test_components_docs_tableau_workspace(
    update_snippets: bool,
    update_screenshots: bool,
    get_selenium_driver,
) -> None:
    with ExitStack() as stack:
        context = stack.enter_context(
            isolated_snippet_generation_environment(
                should_update_snippets=update_snippets,
                snapshot_base_dir=SNIPPETS_DIR,
                global_snippet_replace_regexes=[
                    MASK_VENV,
                    MASK_USING_LOG_MESSAGE,
                    MASK_MY_PROJECT,
                ],
            )
        )
        stack.enter_context(
            environ(
                {
                    "TABLEAU_CONNECTED_APP_CLIENT_ID": "XX",
                    "TABLEAU_CONNECTED_APP_SECRET_ID": "XX",
                    "TABLEAU_CONNECTED_APP_SECRET_VALUE": "XX",
                    "TABLEAU_USERNAME": "test_user",
                    "TABLEAU_SITE_NAME": "test_site",
                    "TABLEAU_POD_NAME": "10ax",
                }
            )
        )
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-tableau", "dagster-tableau"),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-tableau'}",
            snippet_path=f"{context.get_next_snip_number()}-add-tableau.txt",
            print_cmd="uv add dagster-tableau",
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # scaffold tableau component
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_tableau.TableauComponent tableau_ingest",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-tableau-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # Populate the scaffolded component with proper configuration
        context.create_file(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_tableau.TableauComponent

                attributes:
                  workspace:
                    type: cloud
                    connected_app_client_id: "{{ env.TABLEAU_CONNECTED_APP_CLIENT_ID }}"
                    connected_app_secret_id: "{{ env.TABLEAU_CONNECTED_APP_SECRET_ID }}"
                    connected_app_secret_value: "{{ env.TABLEAU_CONNECTED_APP_SECRET_VALUE }}"
                    username: "{{ env.TABLEAU_USERNAME }}"
                    site_name: "{{ env.TABLEAU_SITE_NAME }}"
                    pod_name: "{{ env.TABLEAU_POD_NAME }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-populated-component.yaml",
        )

        # copy test_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_tableau_utils.py",
            Path("my_project") / "defs" / "tableau_ingest" / "test_tableau_utils.py",
        )

        _swap_to_mock_tableau_component(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_tableau.TableauComponent

                attributes:
                  workspace:
                    type: cloud
                    connected_app_client_id: "{{ env.TABLEAU_CONNECTED_APP_CLIENT_ID }}"
                    connected_app_secret_id: "{{ env.TABLEAU_CONNECTED_APP_SECRET_ID }}"
                    connected_app_secret_value: "{{ env.TABLEAU_CONNECTED_APP_SECRET_VALUE }}"
                    username: "{{ env.TABLEAU_USERNAME }}"
                    site_name: "{{ env.TABLEAU_SITE_NAME }}"
                    pod_name: "{{ env.TABLEAU_POD_NAME }}"
                  translation:
                    group_name: tableau_data
                    description: "Tableau {{ data.content_type.value }}: {{ data.properties.name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_tableau_component(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation for a specific data type (sheet)
        context.create_file(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_tableau.TableauComponent

                attributes:
                  workspace:
                    type: cloud
                    connected_app_client_id: "{{ env.TABLEAU_CONNECTED_APP_CLIENT_ID }}"
                    connected_app_secret_id: "{{ env.TABLEAU_CONNECTED_APP_SECRET_ID }}"
                    connected_app_secret_value: "{{ env.TABLEAU_CONNECTED_APP_SECRET_VALUE }}"
                    username: "{{ env.TABLEAU_USERNAME }}"
                    site_name: "{{ env.TABLEAU_SITE_NAME }}"
                    pod_name: "{{ env.TABLEAU_POD_NAME }}"
                  translation:
                    for_sheet:
                      tags:
                        is_sheet: "true"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-sheet-translation.yaml",
        )

        _swap_to_mock_tableau_component(
            Path("my_project") / "defs" / "tableau_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs --columns name,kinds,tags",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
