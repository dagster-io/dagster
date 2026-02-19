import shutil
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import ExitStack
from pathlib import Path
from typing import Any

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
    / "powerbi-component"
)


def _swap_to_mock_powerbi_component(path: Path) -> None:
    path.write_text(
        path.read_text().replace(
            "dagster_powerbi.PowerBIWorkspaceComponent",
            "my_project.defs.powerbi_ingest.test_powerbi_utils.MockPowerBIComponent",
        )
    )


def test_components_docs_powerbi_workspace(
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
                    "POWERBI_API_TOKEN": "XX",
                    "POWERBI_WORKSPACE_ID": "XX",
                    "POWERBI_CLIENT_ID": "XX",
                    "POWERBI_CLIENT_SECRET": "XX",
                    "POWERBI_TENANT_ID": "XX",
                }
            )
        )
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-powerbi", "dagster-powerbi"),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-powerbi'}",
            snippet_path=f"{context.get_next_snip_number()}-add-powerbi.txt",
            print_cmd="uv add dagster-powerbi",
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # scaffold powerbi component
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_powerbi.PowerBIWorkspaceComponent powerbi_ingest",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-powerbi-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # Populate the scaffolded component with proper configuration
        context.create_file(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_powerbi.PowerBIWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: "{{ env.POWERBI_WORKSPACE_ID }}"
                    credentials:
                      client_id: "{{ env.POWERBI_CLIENT_ID }}"
                      client_secret: "{{ env.POWERBI_CLIENT_SECRET }}"
                      tenant_id: "{{ env.POWERBI_TENANT_ID }}"

                    # Alternatively, you can use an API access token
                    # credentials:
                    #   token: "{{ env.POWERBI_API_TOKEN }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-populated-component.yaml",
        )

        # copy test_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_powerbi_utils.py",
            Path("my_project") / "defs" / "powerbi_ingest" / "test_powerbi_utils.py",
        )

        _swap_to_mock_powerbi_component(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with semantic model selector
        context.create_file(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_powerbi.PowerBIWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: "{{ env.POWERBI_WORKSPACE_ID }}"
                    credentials:
                      client_id: "{{ env.POWERBI_CLIENT_ID }}"
                      client_secret: "{{ env.POWERBI_CLIENT_SECRET }}"
                      tenant_id: "{{ env.POWERBI_TENANT_ID }}"
                  enable_semantic_model_refresh: True
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )
        _swap_to_mock_powerbi_component(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs --assets 'key:semantic_model*' --columns name,kinds,is_executable",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        context.create_file(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_powerbi.PowerBIWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: "{{ env.POWERBI_WORKSPACE_ID }}"
                    credentials:
                      client_id: "{{ env.POWERBI_CLIENT_ID }}"
                      client_secret: "{{ env.POWERBI_CLIENT_SECRET }}"
                      tenant_id: "{{ env.POWERBI_TENANT_ID }}"
                  enable_semantic_model_refresh:
                    - Sales Data Model
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_powerbi_component(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs --assets 'key:semantic_model*' --columns name,kinds,is_executable",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_powerbi.PowerBIWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: "{{ env.POWERBI_WORKSPACE_ID }}"
                    credentials:
                      client_id: "{{ env.POWERBI_CLIENT_ID }}"
                      client_secret: "{{ env.POWERBI_CLIENT_SECRET }}"
                      tenant_id: "{{ env.POWERBI_TENANT_ID }}"
                  translation:
                    group_name: powerbi_data
                    description: "PowerBI {{ data.content_type.value }}: {{ data.properties.name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_powerbi_component(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation for a specific data type (semantic model)
        context.create_file(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_powerbi.PowerBIWorkspaceComponent

                attributes:
                  workspace:
                    workspace_id: "{{ env.POWERBI_WORKSPACE_ID }}"
                    credentials:
                      client_id: "{{ env.POWERBI_CLIENT_ID }}"
                      client_secret: "{{ env.POWERBI_CLIENT_SECRET }}"
                      tenant_id: "{{ env.POWERBI_TENANT_ID }}"
                  enable_semantic_model_refresh:
                    - Sales Data Model
                  translation:
                    for_semantic_model:
                      tags:
                        is_semantic_model: "true"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-semantic-translation.yaml",
        )

        _swap_to_mock_powerbi_component(
            Path("my_project") / "defs" / "powerbi_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs --columns name,kinds,tags",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
