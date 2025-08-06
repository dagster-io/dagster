import textwrap
from contextlib import ExitStack
from pathlib import Path

from dagster_dg_core.utils import activate_venv

from docs_snippets_tests.snippet_checks.guides.components.utils import DAGSTER_ROOT
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
    / "python-script-component"
)


def test_components_docs_python_script(
    update_snippets: bool,
    update_screenshots: bool,
    get_selenium_driver,
) -> None:
    with (
        isolated_snippet_generation_environment(
            should_update_snippets=update_snippets,
            snapshot_base_dir=SNIPPETS_DIR,
            global_snippet_replace_regexes=[
                MASK_VENV,
                MASK_USING_LOG_MESSAGE,
                MASK_MY_PROJECT,
            ],
        ) as context,
        ExitStack() as stack,
    ):
        # 1-scaffold-project.txt: Project creation
        context.run_command_and_snippet_output(
            cmd="create-dagster project my-project --uv-sync --use-editable-dagster && cd my-project/src",
            snippet_path=f"{context.get_next_snip_number()}-scaffold-project.txt",
            snippet_replace_regex=[
                ("--uv-sync --use-editable-dagster ", ""),
                ("create-dagster", "uvx create-dagster"),
            ],
            ignore_output=True,
        )

        stack.enter_context(activate_venv("../.venv"))

        # 2-scaffold-python-script-component.txt: Component scaffolding
        context.run_command_and_snippet_output(
            cmd="dg scaffold defs dagster.PythonScriptComponent generate_revenue_report",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-scaffold-python-script-component.txt",
        )

        # 3-tree.txt: Project structure
        context.run_command_and_snippet_output(
            cmd="tree my_project/defs",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-tree.txt",
            custom_comparison_fn=compare_tree_output,
        )

        # 4-process-sales-data.py: Simple Python script
        context.create_file(
            Path("my_project")
            / "defs"
            / "generate_revenue_report"
            / "process_sales_data.py",
            contents=textwrap.dedent(
                """\
                import pandas as pd

                # Sample sales data (in a real scenario, this might come from a database or file)
                sales_data = {
                    "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                    "product": ["A", "B", "A"],
                    "quantity": [10, 5, 8],
                    "price": [100.0, 200.0, 100.0],
                }

                df = pd.DataFrame(sales_data)
                df["revenue"] = df["quantity"] * df["price"]

                # Calculate total revenue
                total_revenue = df["revenue"].sum()

                print(f"Generated revenue report with total revenue: ${total_revenue}")  # noqa: T201
                print(f"Number of transactions: {len(df)}")  # noqa: T201
                print(f"Average transaction: ${df['revenue'].mean():.2f}")  # noqa: T201
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-process-sales-data.py",
        )

        # 5-customized-component.yaml: Basic component configuration
        context.create_file(
            Path("my_project") / "defs" / "generate_revenue_report" / "defs.yaml",
            contents=textwrap.dedent(
                """\
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: process_sales_data.py
                  assets:
                    - key: sales_revenue_report
                      description: "Daily sales revenue report generated from transaction data"
                      group_name: "analytics"
                      kinds: ["python", "report"]
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-customized-component.yaml",
        )

        # 6-launch.txt: Launch command (static content)
        context.create_file(
            Path(
                "dummy_file_for_launch.txt"
            ),  # Create dummy file just to generate snippet
            contents="dg dev",
            snippet_path=SNIPPETS_DIR / f"{context.get_next_snip_number()}-launch.txt",
        )

        # 7-list-defs.txt: List definitions output
        context.run_command_and_snippet_output(
            cmd="dg list defs",
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-list-defs.txt",
        )

        # 8-advanced-pipes-script.py: Advanced script with Dagster Pipes
        context.create_file(
            Path("my_project")
            / "defs"
            / "generate_revenue_report"
            / "advanced_script.py",
            contents=textwrap.dedent(
                """\
                import pandas as pd
                from dagster_pipes import open_dagster_pipes

                # Sample sales data (in a real scenario, this might come from a database or file)
                sales_data = {
                    "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                    "product": ["A", "B", "A"],
                    "quantity": [10, 5, 8],
                    "price": [100.0, 200.0, 100.0],
                }

                with open_dagster_pipes() as context:
                    df = pd.DataFrame(sales_data)
                    df["revenue"] = df["quantity"] * df["price"]
                    
                    # Calculate total revenue
                    total_revenue = df["revenue"].sum()
                    
                    # Log the result to Dagster
                    context.log.info(f"Generated revenue report with total revenue: ${total_revenue}")
                    context.log.info(f"Processed {len(df)} transactions")
                    
                    # Report asset materialization with rich metadata
                    context.report_asset_materialization(
                        metadata={
                            "total_revenue": total_revenue,
                            "num_transactions": len(df),
                            "average_transaction": df["revenue"].mean(),
                            "top_product": df.loc[df["revenue"].idxmax(), "product"],
                        }
                    )
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-advanced-pipes-script.py",
        )

        # 9-multiple-scripts-component.yaml: Multiple scripts configuration
        context.create_file(
            Path("dummy_multiple_scripts.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: process_sales_data.py
                  assets:
                    - key: sales_revenue_report
                      description: "Daily sales revenue report"
                      group_name: "analytics"
                ---
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: process_customer_data.py
                  assets:
                    - key: customer_summary_stats
                      description: "Summary statistics for customer data"
                      group_name: "analytics"
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-multiple-scripts-component.yaml",
        )

        # 10-dependencies-component.yaml: Dependencies example
        context.create_file(
            Path("dummy_dependencies.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: process_sales_data.py
                  assets:
                    - key: sales_revenue_report
                      description: "Daily sales revenue report"
                      group_name: "analytics"
                ---
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: process_customer_data.py
                  assets:
                    - key: customer_summary_stats
                      description: "Summary statistics for customer data"
                      group_name: "analytics"
                      deps: [sales_revenue_report]
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-dependencies-component.yaml",
        )

        # 11-automation-component.yaml: Automation conditions
        context.create_file(
            Path("dummy_automation.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: process_sales_data.py
                  assets:
                    - key: sales_revenue_report
                      description: "Daily sales revenue report"
                      group_name: "analytics"
                      automation_condition: "{{ automation_condition.on_cron('@daily') }}"
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-automation-component.yaml",
        )

        # 12-tree-with-subdirs.txt: Subdirectory structure (static content)
        context.create_file(
            Path("dummy_tree.txt"),
            contents=textwrap.dedent(
                """\
                my-project/src/my_project/defs/generate_revenue_report/
                ├── defs.yaml
                ├── scripts/
                │   ├── process_sales_data.py
                │   └── generate_reports.py
                └── utils/
                    └── data_helpers.py
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-tree-with-subdirs.txt",
        )

        # 13-subdirectory-component.yaml: Component referencing script in subdirectory
        context.create_file(
            Path("dummy_subdirectory.yaml"),
            contents=textwrap.dedent(
                """\
                type: dagster.PythonScriptComponent

                attributes:
                  execution:
                    path: scripts/process_sales_data.py
                  assets:
                    - key: sales_revenue_report
                """
            ),
            snippet_path=SNIPPETS_DIR
            / f"{context.get_next_snip_number()}-subdirectory-component.yaml",
        )
