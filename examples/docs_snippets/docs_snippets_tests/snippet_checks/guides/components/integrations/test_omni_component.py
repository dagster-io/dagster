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
    / "omni-component"
)


def _swap_to_mock_omni_component(path: Path) -> None:
    path.write_text(
        path.read_text().replace(
            "dagster_omni.OmniComponent",
            "my_project.defs.omni_ingest.test_omni_utils.MockOmniComponent",
        )
    )


def test_components_docs_omni_workspace(
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
                    "OMNI_API_KEY": "test_api_key",
                }
            )
        )
        # Scaffold code location
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("--editable.*dagster-omni", "dagster-omni"),
                ("create-dagster", "dg project scaffold --name"),
            ],
            ignore_output=True,
        )

        context.run_command_and_snippet_output(
            cmd=f"uv add --editable {EDITABLE_DIR / 'dagster-omni'}",
            snippet_path=f"{context.get_next_snip_number()}-add-omni.txt",
            print_cmd="uv add dagster-omni",
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # scaffold omni component
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster_omni.OmniComponent omni_ingest",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-omni-component.txt",
        )

        # Tree the project
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        context.check_file(
            Path("my_project") / "defs" / "omni_ingest" / "defs.yaml",
            snippet_path=f"{context.get_next_snip_number()}-component.yaml",
        )

        # Populate the scaffolded component with proper configuration
        context.create_file(
            Path("my_project") / "defs" / "omni_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_omni.OmniComponent

                attributes:
                  workspace:
                    base_url: https://your-company.omniapp.co
                    api_key: "{{ env.OMNI_API_KEY }}"
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-populated-component.yaml",
        )

        # copy test_utils.py to my-project
        shutil.copy(
            Path(__file__).parent / "test_omni_utils.py",
            Path("my_project") / "defs" / "omni_ingest" / "test_omni_utils.py",
        )

        _swap_to_mock_omni_component(
            Path("my_project") / "defs" / "omni_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # Update component.yaml with translation
        context.create_file(
            Path("my_project") / "defs" / "omni_ingest" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster_omni.OmniComponent

                attributes:
                  workspace:
                    base_url: https://your-company.omniapp.co
                    api_key: "{{ env.OMNI_API_KEY }}"
                  translation:
                    group_name: analytics
                    tags:
                      domain: bi
                """
            ),
            snippet_path=f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        _swap_to_mock_omni_component(
            Path("my_project") / "defs" / "omni_ingest" / "defs.yaml"
        )
        context.run_command_and_snippet_output(
            cmd="dg list defs --columns name,group,tags",
            snippet_path=f"{context.get_next_snip_number()}-list-defs.txt",
        )
