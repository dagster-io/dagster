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
    / "sigma-component"
)


def _swap_to_mock_sigma_component(path: Path) -> None:
    path.write_text(
        path.read_text().replace(
            "dagster_sigma.SigmaOrganizationComponent",
            "my_project.defs.sigma_ingest.test_sigma_utils.MockSigmaComponent",
        )
    )


def test_components_docs_sigma_organization(
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
                    "SIGMA_BASE_URL": "https://aws-api.sigmacomputing.com",
                    "SIGMA_CLIENT_ID": "XX",
                    "SIGMA_CLIENT_SECRET": "XX",
                }
            )
        )
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-sigma", "dagster-sigma"),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-sigma'}",
            snippet_path=f"{context.get_next_snip_number()}-add-sigma.txt",
            print_cmd="uv add dagster-sigma",
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # scaffold sigma component
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_sigma.SigmaOrganizationComponent sigma_ingest",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-sigma-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # Populate the scaffolded component with proper configuration
        context.create_file(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_sigma.SigmaOrganizationComponent

                attributes:
                  organization:
                    base_url: "{{ env.SIGMA_BASE_URL }}"
                    client_id: "{{ env.SIGMA_CLIENT_ID }}"
                    client_secret: "{{ env.SIGMA_CLIENT_SECRET }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-populated-component.yaml",
        )

        # copy test_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_sigma_utils.py",
            Path("my_project") / "defs" / "sigma_ingest" / "test_sigma_utils.py",
        )

        _swap_to_mock_sigma_component(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with sigma_filter
        context.create_file(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_sigma.SigmaOrganizationComponent

                attributes:
                  organization:
                    base_url: "{{ env.SIGMA_BASE_URL }}"
                    client_id: "{{ env.SIGMA_CLIENT_ID }}"
                    client_secret: "{{ env.SIGMA_CLIENT_SECRET }}"
                  sigma_filter:
                    workbook_folders:
                      - ["My Documents"]
                    include_unused_datasets: false
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_sigma.SigmaOrganizationComponent

                attributes:
                  organization:
                    base_url: "{{ env.SIGMA_BASE_URL }}"
                    client_id: "{{ env.SIGMA_CLIENT_ID }}"
                    client_secret: "{{ env.SIGMA_CLIENT_SECRET }}"
                  translation:
                    group_name: sigma_data
                    description: "Sigma {{ data.__class__.__name__ }}: {{ data.workbook.name if data.__class__.__name__ == 'SigmaWorkbookTranslatorData' else data.dataset.name }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_sigma_component(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation for a specific data type (workbook)
        context.create_file(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_sigma.SigmaOrganizationComponent

                attributes:
                  organization:
                    base_url: "{{ env.SIGMA_BASE_URL }}"
                    client_id: "{{ env.SIGMA_CLIENT_ID }}"
                    client_secret: "{{ env.SIGMA_CLIENT_SECRET }}"
                  translation:
                    for_workbook:
                      tags:
                        is_workbook: "true"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-workbook-translation.yaml",
        )

        _swap_to_mock_sigma_component(
            Path("my_project") / "defs" / "sigma_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs --columns name,kinds,tags",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
